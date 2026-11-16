/**
 * J.A.R.V.I.S. ECOSYSTEM - MONGOOSE SCHEMA MODELING & NoSQL DOCUMENT STORE (MONGO)
 * Implements:
 *   1. Schema Modeling (Mongo via Mongoose Schemas & Types)
 *   2. Embedding vs Referencing Relationships
 *   3. Indexing for Query Performance (Mongo B-Tree & Compound Indexes)
 *   4. CRUD Operations (Create, Read, Update, Delete)
 *   5. Aggregation Pipelines ($match, $group, $sort, $project)
 */

const mongoose = require("mongoose");

// =====================================================================
// 1. EMBEDDED SUB-DOCUMENT SCHEMA (Embedding Pattern)
// =====================================================================
const PreferenceSchema = new mongoose.Schema({
  theme: { type: String, default: "dark-holographic" },
  ttsVoice: { type: String, default: "af_heart" },
  audioMuted: { type: Boolean, default: false },
  hologramColor: { type: String, default: "#00e5ff" }
}, { _id: false });

// =====================================================================
// 2. PRIMARY DOCUMENT SCHEMA (Mongo Modeling & Indexing)
// =====================================================================
const UserProfileSchema = new mongoose.Schema({
  username: {
    type: String,
    required: true,
    unique: true,
    trim: true
  },
  email: {
    type: String,
    required: true,
    unique: true,
    lowercase: true
  },
  // Embedding Pattern: Embedded Sub-document directly inside parent document
  preferences: {
    type: PreferenceSchema,
    default: () => ({})
  },
  tags: [String],
  createdAt: {
    type: Date,
    default: Date.now
  }
});

// Indexing for query performance (Mongo)
UserProfileSchema.index({ username: 1 });
UserProfileSchema.index({ email: 1 });
UserProfileSchema.index({ tags: 1, createdAt: -1 });

// =====================================================================
// 3. REFERENCED DOCUMENT SCHEMA (Referencing Pattern)
// =====================================================================
const OperationalNoteSchema = new mongoose.Schema({
  // Referencing Pattern: References parent User document by ObjectId
  userRefId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: "UserProfile",
    required: true,
    index: true
  },
  category: {
    type: String,
    required: true,
    enum: ["automation", "diagnostics", "episodic_memory", "system_health"]
  },
  title: {
    type: String,
    required: true
  },
  content: {
    type: String,
    required: true
  },
  latencyMs: {
    type: Number,
    default: 0
  },
  createdAt: {
    type: Date,
    default: Date.now,
    index: true
  }
});

// Compound Index for high-performance category range queries
OperationalNoteSchema.index({ category: 1, createdAt: -1 });

// Models
const UserProfile = mongoose.models.UserProfile || mongoose.model("UserProfile", UserProfileSchema);
const OperationalNote = mongoose.models.OperationalNote || mongoose.model("OperationalNote", OperationalNoteSchema);

// =====================================================================
// 4. CRUD OPERATIONS (MONGO)
// =====================================================================
class MongoService {
  // CREATE: Insert new document
  static async createProfile(username, email, preferences = {}) {
    const profile = await UserProfile.create({
      username,
      email,
      preferences,
      tags: ["edge_user", "developer"]
    });
    return profile;
  }

  // READ: Query documents with filtering and projection
  static async findProfilesByTag(tag, limit = 20) {
    const profiles = await UserProfile.find({ tags: tag })
      .select("username email preferences createdAt")
      .limit(limit)
      .lean();
    return profiles;
  }

  // UPDATE: Mutate document fields
  static async updatePreferences(userId, newPreferences) {
    const updated = await UserProfile.findByIdAndUpdate(
      userId,
      { $set: { preferences: newPreferences } },
      { new: true, runValidators: true }
    );
    return updated;
  }

  // DELETE: Remove document
  static async deleteProfile(userId) {
    const result = await UserProfile.deleteOne({ _id: userId });
    return result.deletedCount > 0;
  }

  // CREATE Note referencing User
  static async createNote(userRefId, category, title, content, latencyMs = 25) {
    const note = await OperationalNote.create({
      userRefId,
      category,
      title,
      content,
      latencyMs
    });
    return note;
  }

  // =====================================================================
  // 5. AGGREGATION PIPELINES ($match, $group, $sort, $project)
  // =====================================================================
  static async runCategoryAggregationPipeline() {
    /**
     * Executes a 4-stage MongoDB Aggregation Pipeline:
     * Stage 1: $match   - Filter documents where latencyMs > 0
     * Stage 2: $group   - Group by category, compute count and average latency
     * Stage 3: $sort    - Sort by totalNotes in descending order (-1)
     * Stage 4: $project - Shape output document format
     */
    const pipeline = [
      {
        $match: {
          latencyMs: { $gt: 0 }
        }
      },
      {
        $group: {
          _id: "$category",
          totalNotes: { $sum: 1 },
          avgLatencyMs: { $avg: "$latencyMs" }
        }
      },
      {
        $sort: {
          totalNotes: -1
        }
      },
      {
        $project: {
          _id: 0,
          category: "$_id",
          totalNotes: 1,
          avgLatencyMs: { $round: ["$avgLatencyMs", 2] }
        }
      }
    ];

    const results = await OperationalNote.aggregate(pipeline);
    return results;
  }
}

module.exports = {
  UserProfile,
  OperationalNote,
  MongoService
};
