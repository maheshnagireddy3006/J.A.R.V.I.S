"""
JARVIS: EDGE-FIRST GRAPH-AGENT ECOSYSTEM - BRAIN & ORCHESTRATION ENGINE
Integrates:
  1. LangGraph Async Stateful Workflow with Intent Routing & Automated Self-Correction Loop
  2. Local ChromaDB Vector Memory with CPU-bound BGE Embeddings
  3. Local System Automation Tools (Health, App Launcher, Shell Execution)
  4. Direct Ollama API / LangChain Interface
"""

import os
import sys
import json
import time
import psutil
import shutil
import logging
import traceback
import subprocess
from typing import Optional, List, Dict, Any, Callable, cast
from typing_extensions import TypedDict
from pathlib import Path

import re
import chromadb
from chromadb.utils import embedding_functions
try:
    from langchain_ollama import ChatOllama
except ImportError:
    from langchain_community.chat_models import ChatOllama  # type: ignore
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END

import config

logger = logging.getLogger("JarvisBrain")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


# =====================================================================
# 1. LOCAL VECTOR MEMORY SUBSYSTEM (CHROMADB + CPU BGE EMBEDDINGS)
# =====================================================================
class MemorySubsystem:
    """
    Local ChromaDB vector memory operating entirely on CPU.
    Stores user preferences, factual recall, and session context.
    """
    def __init__(self, persist_dir: Path = config.CHROMA_PERSIST_DIR):
        self.persist_dir = str(persist_dir)
        logger.info(f"Initializing persistent ChromaDB client at: {self.persist_dir}")
        self.client = chromadb.PersistentClient(path=self.persist_dir)

        # Force CPU device for sentence transformer to preserve 6GB VRAM for Ollama
        try:
            self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=config.EMBEDDING_MODEL_NAME,
                device=config.DEVICE_EMBED
            )
            logger.info(f"Loaded CPU Embedding model: {config.EMBEDDING_MODEL_NAME}")
        except Exception as e:
            logger.warning(f"Defaulting to standard embedding function due to: {e}")
            self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()

        self.collection = self.client.get_or_create_collection(
            name=config.CHROMA_COLLECTION_NAME,
            embedding_function=self.embedding_fn,  # type: ignore[arg-type]
            metadata={"description": "Jarvis episodic & operational memory"}
        )

    def store_memory(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Persist a memory snippet into ChromaDB."""
        if not text or not text.strip():
            return False
        try:
            doc_id = f"mem_{int(time.time() * 1000)}"
            meta = metadata or {"source": "conversation", "timestamp": time.time()}
            self.collection.add(
                documents=[text.strip()],
                metadatas=[meta],
                ids=[doc_id]
            )
            logger.info(f"Saved memory [{doc_id}]: {text[:60]}...")
            return True
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            return False

    def recall_memories(self, query: str, n_results: int = config.MEMORY_QUERY_TOP_K) -> List[str]:
        """Retrieve most relevant memories via vector semantic search."""
        if not query or not query.strip():
            return []
        try:
            count = self.collection.count()
            if count == 0:
                return []
            k = min(n_results, count)
            results = self.collection.query(
                query_texts=[query],
                n_results=k
            )
            docs_list = results.get("documents")
            docs = docs_list[0] if docs_list and len(docs_list) > 0 else []
            return [d for d in docs if d]
        except Exception as e:
            logger.error(f"Failed to recall memories: {e}")
            return []


# =====================================================================
# 2. LOCAL AUTOMATION TOOLS (EDGE SYSTEM CONTROL)
# =====================================================================
class LocalTools:
    """Hardware and OS-level operations executed directly on the host machine."""

    @staticmethod
    def get_system_health() -> Dict[str, Any]:
        """Reads CPU, RAM, Disk, and Battery metrics via psutil."""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_count_logical = psutil.cpu_count(logical=True)
            cpu_count_physical = psutil.cpu_count(logical=False)
            
            vm = psutil.virtual_memory()
            ram_total_gb = round(vm.total / (1024 ** 3), 2)
            ram_used_gb = round(vm.used / (1024 ** 3), 2)
            ram_percent = vm.percent

            # Disk usage for Windows drives (direct check avoiding partition probe delays)
            disks = {}
            try:
                usage = psutil.disk_usage("C:\\")
                disks["C:\\"] = {
                    "total_gb": round(usage.total / (1024 ** 3), 1),
                    "free_gb": round(usage.free / (1024 ** 3), 1),
                    "percent_used": usage.percent
                }
                if os.path.exists("D:\\"):
                    d_usage = psutil.disk_usage("D:\\")
                    disks["D:\\"] = {
                        "total_gb": round(d_usage.total / (1024 ** 3), 1),
                        "free_gb": round(d_usage.free / (1024 ** 3), 1),
                        "percent_used": d_usage.percent
                    }
            except Exception:
                pass

            # Battery if available
            battery = psutil.sensors_battery()
            battery_info = None
            if battery:
                battery_info = {
                    "percent": battery.percent,
                    "power_plugged": battery.power_plugged,
                    "seconds_left": battery.secsleft if battery.secsleft != psutil.POWER_TIME_UNLIMITED else "Plugged in"
                }

            return {
                "status": "success",
                "cpu": {
                    "usage_percent": cpu_percent,
                    "cores_physical": cpu_count_physical,
                    "cores_logical": cpu_count_logical
                },
                "ram": {
                    "total_gb": ram_total_gb,
                    "used_gb": ram_used_gb,
                    "percent_used": ram_percent
                },
                "disks": disks,
                "battery": battery_info
            }
        except Exception as e:
            logger.error(f"Tool error in get_system_health: {e}")
            raise RuntimeError(f"System health query failed: {str(e)}")

    @staticmethod
    def launch_application(app_identifier: str) -> str:
        """
        Launches standard Windows applications or opens a file/url.
        Resolves common names like notepad, calc, chrome, terminal, explorer.
        """
        app_map = {
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "calc": "calc.exe",
            "terminal": "wt.exe",
            "cmd": "cmd.exe",
            "powershell": "powershell.exe",
            "explorer": "explorer.exe",
            "taskmgr": "taskmgr.exe",
            "task manager": "taskmgr.exe",
            "chrome": "chrome.exe",
            "edge": "msedge.exe",
            "code": "code.cmd"
        }

        clean_id = app_identifier.strip().lower()
        target = app_map.get(clean_id, app_identifier)

        try:
            # Check if it's an executable in PATH or direct path
            if shutil.which(target) or os.path.isabs(target) or target in app_map.values():
                subprocess.Popen(target, shell=True)
                return f"Successfully initiated launch sequence for: {target}"
            else:
                # Attempt Windows os.startfile
                if hasattr(os, "startfile"):
                    os.startfile(target)  # type: ignore[attr-defined]
                else:
                    subprocess.Popen(target, shell=True)
                return f"Opened file or application via OS handler: {target}"
        except Exception as e:
            logger.error(f"Tool error in launch_application: {e}")
            raise RuntimeError(f"Failed to launch '{app_identifier}': {str(e)}")

    @staticmethod
    def execute_shell_command(command: str) -> str:
        """
        Executes a PowerShell command in a secure, controlled subprocess with timeout.
        """
        # Forbidden command filter to protect local host integrity
        forbidden = ["format", "del /f /s /q c:", "rmdir /s /q c:", "reg delete"]
        cmd_lower = command.lower()
        for f in forbidden:
            if f in cmd_lower:
                raise PermissionError(f"Command '{command}' blocked by safety guardrail.")

        try:
            proc = subprocess.run(
                ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=15,
                check=False
            )
            stdout = proc.stdout.strip()
            stderr = proc.stderr.strip()
            if proc.returncode != 0:
                raise RuntimeError(f"Command exited with code {proc.returncode}. Error: {stderr or stdout}")
            return stdout if stdout else "Command completed successfully with no output."
        except subprocess.TimeoutExpired:
            raise TimeoutError(f"Command '{command}' timed out after 15 seconds.")
        except Exception as e:
            raise RuntimeError(f"Shell execution failed: {str(e)}")

    @staticmethod
    def search_local_files(directory: str, pattern: str) -> List[str]:
        """Find files matching pattern inside a given directory."""
        search_path = Path(directory)
        if not search_path.exists():
            raise FileNotFoundError(f"Target directory does not exist: {directory}")

        matches = []
        try:
            for path in search_path.rglob(pattern):
                if len(matches) >= 15:
                    break
                matches.append(str(path))
            return matches
        except Exception as e:
            raise RuntimeError(f"File search failed: {str(e)}")


# =====================================================================
# 3. LANGGRAPH STATE DEFINITION
# =====================================================================
class JarvisState(TypedDict):
    user_input: str
    messages: List[Dict[str, str]]
    intent: str  # 'automation' | 'memory_query' | 'conversation'
    tool_name: Optional[str]
    tool_args: Optional[Dict[str, Any]]
    tool_result: Optional[str]
    error_trace: Optional[str]
    retry_count: int
    memory_context: Optional[str]
    final_response: str


# =====================================================================
# 4. ORCHESTRATION & SELF-CORRECTION WORKFLOW
# =====================================================================
class JarvisBrain:
    """
    Stateful LangGraph Agent orchestrating Intent Routing, Tool Execution,
    Vector Memory Retrieval, and Automated Error Self-Correction.
    """

    def __init__(self, log_callback: Optional[Callable[[str, str], None]] = None):
        """
        Args:
            log_callback: Optional callable(tag: str, message: str) to stream UI updates.
        """
        self.log_callback = log_callback or (lambda tag, msg: logger.info(f"[{tag}] {msg}"))
        self.memory = MemorySubsystem()
        self.tools = LocalTools()

        # Initialize Ollama LLM
        self.log("SYSTEM", f"Connecting to Ollama at {config.OLLAMA_BASE_URL} ({config.OLLAMA_MODEL})...")
        self.llm = ChatOllama(
            base_url=config.OLLAMA_BASE_URL,
            model=config.OLLAMA_MODEL,
            temperature=config.OLLAMA_TEMPERATURE,
            client_kwargs={"timeout": config.OLLAMA_TIMEOUT}
        )

        # Build LangGraph State Machine
        self.workflow = self._build_graph()

    def log(self, tag: str, message: str):
        """Helper to pipe internal state transitions to UI or terminal."""
        self.log_callback(tag, message)

    def _build_graph(self) -> Any:
        """Defines the nodes, edges, and conditional branches of the agent."""
        builder = StateGraph(cast(Any, JarvisState))  # type: ignore[arg-type]

        # Add Nodes
        builder.add_node("intent_router", self._node_intent_router)
        builder.add_node("tool_executor", self._node_tool_executor)
        builder.add_node("error_recovery", self._node_error_recovery)
        builder.add_node("memory_retriever", self._node_memory_retriever)
        builder.add_node("response_generator", self._node_response_generator)

        # Entry point
        builder.set_entry_point("intent_router")

        # Routing from intent_router
        builder.add_conditional_edges(
            "intent_router",
            self._route_after_intent,
            {
                "automation": "tool_executor",
                "memory_query": "memory_retriever",
                "conversation": "response_generator"
            }
        )

        # Routing from tool_executor (Self-correction conditional branch)
        builder.add_conditional_edges(
            "tool_executor",
            self._route_after_tool,
            {
                "success": "response_generator",
                "error_recover": "error_recovery",
                "fatal_error": "response_generator"
            }
        )

        # Routing from error_recovery
        builder.add_conditional_edges(
            "error_recovery",
            self._route_after_recovery,
            {
                "retry_tool": "tool_executor",
                "abort_to_response": "response_generator"
            }
        )

        # Direct edges
        builder.add_edge("memory_retriever", "response_generator")
        builder.add_edge("response_generator", END)

        return builder.compile()

    # -------------------------------------------------------------
    # GRAPH NODES
    # -------------------------------------------------------------
    def _node_intent_router(self, state: JarvisState) -> Dict[str, Any]:
        """Classifies user input into automation, memory_query, or conversation."""
        user_input = state["user_input"]
        self.log("ROUTER", f"Analyzing intent for: '{user_input}'")

        system_prompt = (
            "You are the intent router for Jarvis, a localized edge desktop assistant.\n"
            "Analyze the user's input and classify it into one of these intents:\n"
            "1. 'automation': The user wants to inspect system health, launch an application, execute a shell command, or search files.\n"
            "2. 'memory_query': The user asks to recall or remember previously saved personal information, preferences, or notes.\n"
            "3. 'conversation': General conversational queries, Q&A, greetings, code explanation, reasoning.\n\n"
            "If 'automation', select the tool:\n"
            "- 'get_system_health' (args: {})\n"
            "- 'launch_application' (args: {'app_identifier': '<name_or_path>'})\n"
            "- 'execute_shell_command' (args: {'command': '<powershell_cmd>'})\n"
            "- 'search_local_files' (args: {'directory': '<dir_path>', 'pattern': '<glob_pattern>'})\n\n"
            "OUTPUT FORMAT: Strict JSON only. Example:\n"
            "{\n"
            '  "intent": "automation",\n'
            '  "tool_name": "get_system_health",\n'
            '  "tool_args": {}\n'
            "}\n"
            "Do NOT output markdown blocks or conversational text, output ONLY valid JSON."
        )

        try:
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_input)
            ])
            raw = str(response.content).strip()
            # Extract JSON block using regex if wrapped in markdown or extra text
            json_match = re.search(r'\{.*\}', raw, re.DOTALL)
            if json_match:
                raw_json = json_match.group(0)
            else:
                raw_json = raw

            parsed = json.loads(raw_json)
            intent = parsed.get("intent", "conversation")
            tool_name = parsed.get("tool_name")
            tool_args = parsed.get("tool_args", {})

            self.log("ROUTER", f"Classified intent: {intent.upper()} (Tool: {tool_name})")
            return {
                "intent": intent,
                "tool_name": tool_name,
                "tool_args": tool_args,
                "error_trace": None,
                "retry_count": 0
            }
        except Exception as e:
            self.log("WARN", f"Router JSON parsing fallback: {e}. Defaulting to conversation.")
            return {
                "intent": "conversation",
                "tool_name": None,
                "tool_args": None,
                "error_trace": None,
                "retry_count": 0
            }

    def _node_tool_executor(self, state: JarvisState) -> Dict[str, Any]:
        """Executes the requested automation tool and intercepts errors."""
        tool_name = state.get("tool_name")
        tool_args = state.get("tool_args") or {}
        self.log("TOOL", f"Executing tool: '{tool_name}' with args: {tool_args}")

        try:
            if tool_name == "get_system_health":
                result = self.tools.get_system_health()
                result_str = json.dumps(result, indent=2)
            elif tool_name == "launch_application":
                app_id = tool_args.get("app_identifier", "")
                result_str = self.tools.launch_application(app_id)
            elif tool_name == "execute_shell_command":
                cmd = tool_args.get("command", "")
                result_str = self.tools.execute_shell_command(cmd)
            elif tool_name == "search_local_files":
                directory = tool_args.get("directory", str(config.BASE_DIR))
                pattern = tool_args.get("pattern", "*")
                matches = self.tools.search_local_files(directory, pattern)
                result_str = f"Found {len(matches)} files: " + json.dumps(matches)
            else:
                raise ValueError(f"Unknown tool requested: {tool_name}")

            self.log("SUCCESS", f"Tool '{tool_name}' succeeded.")
            return {
                "tool_result": result_str,
                "error_trace": None
            }
        except Exception as e:
            tb = traceback.format_exc()
            self.log("ERROR", f"Tool '{tool_name}' failed: {str(e)}")
            return {
                "tool_result": None,
                "error_trace": f"{str(e)}\n{tb}"
            }

    def _node_error_recovery(self, state: JarvisState) -> Dict[str, Any]:
        """
        AUTOMATED SELF-CORRECTION LOOP:
        Feeds the error traceback back to Llama 3.1 8B to diagnose the failure
        and formulate a corrected tool invocation or fallback.
        """
        tool_name = state.get("tool_name")
        error_trace = state.get("error_trace") or "Unknown error"
        current_retries = state.get("retry_count", 0) + 1

        self.log("RETRY", f"Triggering Self-Correction Loop [Attempt {current_retries}/{config.MAX_SELF_CORRECTION_RETRIES}]")

        prompt = (
            f"The tool '{tool_name}' failed with the following traceback on a Windows 11 machine:\n"
            f"--- ERROR TRACEBACK ---\n{error_trace}\n-----------------------\n"
            f"Original user request: '{state['user_input']}'.\n"
            f"Previous tool arguments: {state.get('tool_args')}.\n\n"
            "Diagnose the root cause (e.g., wrong executable name, path syntax, PowerShell parameter issue).\n"
            "If you can correct the tool call, provide the corrected JSON:\n"
            "{\n"
            '  "action": "retry",\n'
            f'  "tool_name": "{tool_name}",\n'
            '  "tool_args": { ... corrected args ... }\n'
            "}\n"
            "If the error is unrecoverable or a permission/physical limitation, return:\n"
            "{\n"
            '  "action": "abort",\n'
            '  "diagnosis": "<concise explanation of why it failed>"\n'
            "}\n"
            "Return ONLY valid JSON."
        )

        try:
            response = self.llm.invoke([
                SystemMessage(content="You are an autonomous self-healing agent specializing in Windows systems diagnosis."),
                HumanMessage(content=prompt)
            ])
            raw = str(response.content).strip()
            json_match = re.search(r'\{.*\}', raw, re.DOTALL)
            if json_match:
                raw_json = json_match.group(0)
            else:
                raw_json = raw

            parsed = json.loads(raw_json)
            action = parsed.get("action")

            if action == "retry":
                new_args = parsed.get("tool_args", {})
                self.log("RETRY", f"Self-correction proposed corrected args: {new_args}")
                return {
                    "tool_args": new_args,
                    "retry_count": current_retries,
                    "error_trace": None
                }
            else:
                diagnosis = parsed.get("diagnosis", "Tool execution failed and could not be auto-repaired.")
                self.log("WARN", f"Self-correction could not repair tool: {diagnosis}")
                return {
                    "retry_count": current_retries,
                    "tool_result": f"Execution failed. Diagnosis: {diagnosis}"
                }
        except Exception as e:
            self.log("ERROR", f"Error recovery node exception: {e}")
            err_snippet = (error_trace or "Unknown error")[:200]
            return {
                "retry_count": current_retries,
                "tool_result": f"Execution failed: {err_snippet}"
            }

    def _node_memory_retriever(self, state: JarvisState) -> Dict[str, Any]:
        """Retrieves semantic memories from ChromaDB vector store."""
        user_input = state["user_input"]
        self.log("MEMORY", f"Querying local vector database for: '{user_input}'")
        memories = self.memory.recall_memories(user_input, n_results=config.MEMORY_QUERY_TOP_K)
        if memories:
            context = "\n".join([f"- {m}" for m in memories])
            self.log("MEMORY", f"Retrieved {len(memories)} relevant memory snippets.")
        else:
            context = "No previous memories found relevant to this query."
            self.log("MEMORY", "No prior memory associations found.")

        return {"memory_context": context}

    def _node_response_generator(self, state: JarvisState) -> Dict[str, Any]:
        """Synthesizes final conversational response for the user."""
        user_input = state["user_input"]
        intent = state.get("intent", "conversation")
        tool_result = state.get("tool_result")
        memory_context = state.get("memory_context")
        error_trace = state.get("error_trace")

        self.log("AGENT", "Synthesizing final response with Llama 3.1 8B...")

        system_prompt = (
            "You are JARVIS, an ultra-capable, localized edge-first AI assistant.\n"
            "Your personality is professional, concise, intelligent, and subtly witty.\n"
            "Format your answers cleanly. When presenting system data or errors, be direct and informative.\n"
            "Keep voice-readiness in mind: avoid excessively long tables or unpronounceable characters.\n"
        )

        context_blocks = []
        if tool_result:
            context_blocks.append(f"Tool Execution Output:\n{tool_result}")
        if memory_context:
            context_blocks.append(f"Relevant Memory Records:\n{memory_context}")
        if error_trace:
            context_blocks.append(f"Notice: A tool encountered an error:\n{error_trace}")

        full_prompt = f"User Request: {user_input}"
        if context_blocks:
            full_prompt += "\n\n" + "\n\n".join(context_blocks)

        try:
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=full_prompt)
            ])
            raw_content = response.content
            if isinstance(raw_content, str):
                final_text = raw_content.strip()
            elif isinstance(raw_content, list):
                final_text = "".join(str(item) for item in raw_content).strip()
            else:
                final_text = str(raw_content).strip()
        except Exception as e:
            self.log("ERROR", f"LLM generation failed: {e}")
            final_text = f"Sir, I encountered an internal communication error with the local model engine: {str(e)}"

        # Save meaningful conversations or state updates into memory asynchronously
        if len(user_input) > 10 and not user_input.lower().startswith("what is"):
            self.memory.store_memory(
                f"User stated: {user_input} | Jarvis action/reply: {final_text[:120]}",
                {"source": "session_stream", "timestamp": time.time()}
            )

        self.log("AGENT", "Response synthesis complete.")
        return {"final_response": final_text}

    # -------------------------------------------------------------
    # CONDITIONAL ROUTING FUNCTIONS
    # -------------------------------------------------------------
    def _route_after_intent(self, state: JarvisState) -> str:
        intent = state.get("intent", "conversation")
        if intent == "automation" and state.get("tool_name"):
            return "automation"
        elif intent == "memory_query":
            return "memory_query"
        return "conversation"

    def _route_after_tool(self, state: JarvisState) -> str:
        if state.get("error_trace") is None:
            return "success"
        if state.get("retry_count", 0) < config.MAX_SELF_CORRECTION_RETRIES:
            return "error_recover"
        return "fatal_error"

    def _route_after_recovery(self, state: JarvisState) -> str:
        # If error_recovery cleared error_trace and supplied new args, retry tool
        if state.get("error_trace") is None and state.get("tool_args") is not None:
            return "retry_tool"
        return "abort_to_response"

    # -------------------------------------------------------------
    # PUBLIC INVOCATION API
    # -------------------------------------------------------------
    def process_query(self, user_text: str) -> Dict[str, Any]:
        """
        Synchronously or asynchronously runs the complete LangGraph workflow.
        Returns the final state containing 'final_response'.
        """
        initial_state: JarvisState = {
            "user_input": user_text,
            "messages": [],
            "intent": "conversation",
            "tool_name": None,
            "tool_args": None,
            "tool_result": None,
            "error_trace": None,
            "retry_count": 0,
            "memory_context": None,
            "final_response": ""
        }

        final_state = self.workflow.invoke(initial_state)
        return final_state
