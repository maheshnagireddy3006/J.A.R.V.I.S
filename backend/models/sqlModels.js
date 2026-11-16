/**
 * J.A.R.V.I.S. ECOSYSTEM - SEQUELIZE ORM & RELATIONAL SQL MODELS (POSTGRES / SQLITE)
 * Implements:
 *   1. Relational Schema Design with Primary Key & Foreign Keys
 *   2. ORM Usage (Sequelize Models, Associations & Migrations)
 *   3. SQL JOINs (Multi-table relational joins & eager loading)
 *   4. Indexing for Query Performance (SQL Composite & B-Tree Indexes)
 *   5. Filtering, Ordering, Grouping (Complex aggregations)
 *   6. Normalization Basics (Third Normal Form - 3NF Architecture)
 *   7. ACID Transactions (Explicit commit / rollback boundaries)
 */

const { Sequelize, DataTypes, Op } = require("sequelize");
const path = require("path");

// Connect via SQLite or PostgreSQL connection string
const sequelize = new Sequelize({
  dialect: "sqlite",
  storage: path.join(__dirname, "../../data/jarvis_sequelize.sqlite"),
  logging: false
});

// =====================================================================
// 1. RELATIONAL SCHEMA DESIGN WITH PK / FK (3NF NORMALIZED)
// =====================================================================

// Entity 1: User (Primary Entity)
const User = sequelize.define("User", {
  id: {
    type: DataTypes.INTEGER,
    primaryKey: true,
    autoIncrement: true
  },
  username: {
    type: DataTypes.STRING(64),
    allowNull: false,
    unique: true
  },
  email: {
    type: DataTypes.STRING(128),
    allowNull: false,
    unique: true,
    validate: { isEmail: true }
  },
  passwordHash: {
    type: DataTypes.STRING(256),
    allowNull: false
  },
  role: {
    type: DataTypes.ENUM("admin", "operator", "guest"),
    defaultValue: "operator"
  }
}, {
  tableName: "users",
  timestamps: true,
  indexes: [
    { unique: true, fields: ["username"] },
    { unique: true, fields: ["email"] }
  ]
});

// Entity 2: TaskAudit (Foreign Key Entity referencing User)
const TaskAudit = sequelize.define("TaskAudit", {
  id: {
    type: DataTypes.INTEGER,
    primaryKey: true,
    autoIncrement: true
  },
  userId: {
    type: DataTypes.INTEGER,
    allowNull: true,
    references: {
      model: User,
      key: "id"
    },
    onDelete: "SET NULL"
  },
  actionType: {
    type: DataTypes.STRING(64),
    allowNull: false
  },
  toolName: {
    type: DataTypes.STRING(64),
    allowNull: true
  },
  status: {
    type: DataTypes.ENUM("SUCCESS", "FAILED", "RETRY"),
    allowNull: false
  },
  durationMs: {
    type: DataTypes.FLOAT,
    defaultValue: 0.0
  },
  details: {
    type: DataTypes.TEXT,
    allowNull: true
  }
}, {
  tableName: "task_audits",
  timestamps: true,
  // Indexing for query performance
  indexes: [
    { fields: ["userId", "actionType"] },
    { fields: ["status"] },
    { fields: ["createdAt"] }
  ]
});

// Relational Associations (1-to-Many)
User.hasMany(TaskAudit, { foreignKey: "userId", as: "audits" });
TaskAudit.belongsTo(User, { foreignKey: "userId", as: "user" });

// =====================================================================
// 2. SQL JOINS, FILTERING, ORDERING, GROUPING & TRANSACTIONS
// =====================================================================

class RelationalService {
  /**
   * Demonstrates: ACID Transactions with commit & rollback handling
   */
  static async createUserWithInitialAudit(userData, initialAuditDetails) {
    const t = await sequelize.transaction();
    try {
      const user = await User.create(userData, { transaction: t });
      await TaskAudit.create({
        userId: user.id,
        actionType: "user_registration",
        toolName: "auth_service",
        status: "SUCCESS",
        durationMs: 12.5,
        details: initialAuditDetails
      }, { transaction: t });

      await t.commit();
      return user;
    } catch (error) {
      await t.rollback();
      throw new Error(`Transaction aborted: ${error.message}`);
    }
  }

  /**
   * Demonstrates: SQL JOINs with Filtering and Ordering
   * Performs an INNER JOIN between 'users' and 'task_audits'
   */
  static async getUserAuditsWithJoin(username) {
    // ORM Eager Loading JOIN
    const userWithAudits = await User.findOne({
      where: { username },
      include: [
        {
          model: TaskAudit,
          as: "audits",
          where: { status: "SUCCESS" }, // Filtering on joined table
          required: true // Forces INNER JOIN
        }
      ],
      order: [[{ model: TaskAudit, as: "audits" }, "createdAt", "DESC"]] // Ordering
    });

    return userWithAudits;
  }

  /**
   * Demonstrates: Raw SQL JOIN with custom ON clause
   */
  static async executeRawSqlJoin() {
    const query = `
      SELECT u.id, u.username, u.email, t.actionType, t.status, t.durationMs, t.createdAt
      FROM users u
      INNER JOIN task_audits t ON u.id = t.userId
      WHERE t.durationMs > :minDuration
      ORDER BY t.createdAt DESC
      LIMIT 25;
    `;
    const results = await sequelize.query(query, {
      replacements: { minDuration: 0 },
      type: Sequelize.QueryTypes.SELECT
    });
    return results;
  }

  /**
   * Demonstrates: Grouping, Aggregations (COUNT, AVG), and Filtering (GROUP BY, HAVING)
   */
  static async getToolStatisticsGrouped() {
    const stats = await TaskAudit.findAll({
      attributes: [
        "toolName",
        [Sequelize.fn("COUNT", Sequelize.col("id")), "totalInvocations"],
        [Sequelize.fn("AVG", Sequelize.col("durationMs")), "avgDurationMs"]
      ],
      where: {
        toolName: { [Op.ne]: null }
      },
      group: ["toolName"],
      order: [[Sequelize.fn("COUNT", Sequelize.col("id")), "DESC"]]
    });

    return stats;
  }
}

module.exports = {
  sequelize,
  User,
  TaskAudit,
  RelationalService
};
