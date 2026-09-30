/**
 * =========================================================================
 * SaveIQ – AI Savings Goal Tracker
 * Google Apps Script Backend (Code.gs)
 * Integrated with Google Sheets, Groq AI (LLaMA 3.3-70B), and Gmail Services
 * =========================================================================
 */

// Configuration Constants
const SCRIPT_PROP = PropertiesService.getScriptProperties();
const SHEETS_CONFIG = {
  GOALS_TAB: "Goals",
  DEPOSITS_TAB: "Deposits",
  ALERTS_TAB: "AuditAlerts",
  DEFAULT_MODEL: "llama-3.3-70b-versatile"
};

/**
 * Serves the HTML Web App UI
 */
function doGet(e) {
  return HtmlService.createTemplateFromFile("Index")
    .evaluate()
    .setTitle("SaveIQ – AI Savings Goal Tracker")
    .setFaviconUrl("https://img.icons8.com/fluency/48/safe.png")
    .addMetaTag("viewport", "width=device-width, initial-scale=1.0")
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

/**
 * Include helper for modular HTML/CSS/JS templates
 */
function include(filename) {
  return HtmlService.createHtmlOutputFromFile(filename).getContent();
}

/**
 * Initializes the Google Spreadsheet with headers and formatting
 */
function initializeSheetDatabase() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();

  // 1. Goals Tab
  let goalsSheet = ss.getSheetByName(SHEETS_CONFIG.GOALS_TAB);
  if (!goalsSheet) {
    goalsSheet = ss.insertSheet(SHEETS_CONFIG.GOALS_TAB);
    goalsSheet.appendRow([
      "Goal ID", "Goal Name", "Category", "Target Amount ($)", "Current Saved ($)",
      "Progress (%)", "Remaining ($)", "Deadline", "Email Alerts", "User Email",
      "Priority", "Status", "Purpose", "Created At", "Updated At"
    ]);
    goalsSheet.getRange("A1:O1").setBackground("#1e293b").setFontColor("#ffffff").setFontWeight("bold");
    goalsSheet.setFrozenRows(1);
  }

  // 2. Deposits Tab
  let depositsSheet = ss.getSheetByName(SHEETS_CONFIG.DEPOSITS_TAB);
  if (!depositsSheet) {
    depositsSheet = ss.insertSheet(SHEETS_CONFIG.DEPOSITS_TAB);
    depositsSheet.appendRow(["Deposit ID", "Goal ID", "Goal Name", "Amount ($)", "Note", "Date"]);
    depositsSheet.getRange("A1:F1").setBackground("#0f766e").setFontColor("#ffffff").setFontWeight("bold");
    depositsSheet.setFrozenRows(1);
  }

  // 3. Alerts Tab
  let alertsSheet = ss.getSheetByName(SHEETS_CONFIG.ALERTS_TAB);
  if (!alertsSheet) {
    alertsSheet = ss.insertSheet(SHEETS_CONFIG.ALERTS_TAB);
    alertsSheet.appendRow(["Alert ID", "Goal ID", "Goal Name", "Alert Type", "Message", "Recipient", "Sent At"]);
    alertsSheet.getRange("A1:G1").setBackground("#b91c1c").setFontColor("#ffffff").setFontWeight("bold");
    alertsSheet.setFrozenRows(1);
  }

  return { success: true, message: "SaveIQ Database Schema Initialized Successfully!" };
}

/**
 * Retrieve all goals with calculated pace and status metrics
 */
function getGoals() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(SHEETS_CONFIG.GOALS_TAB);
  if (!sheet) {
    initializeSheetDatabase();
    return [];
  }

  const data = sheet.getDataRange().getValues();
  if (data.length <= 1) return [];

  const headers = data[0];
  const goals = [];
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  for (let i = 1; i < data.length; i++) {
    const row = data[i];
    if (!row[0]) continue;

    const target = parseFloat(row[3]) || 0;
    const current = parseFloat(row[4]) || 0;
    const remaining = Math.max(0, target - current);
    const progress = target > 0 ? Math.round((current / target) * 1000) / 10 : 0;
    
    // Parse deadline
    const deadlineVal = row[7];
    const deadlineDate = new Date(deadlineVal);
    const diffTime = deadlineDate.getTime() - today.getTime();
    const daysLeft = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    const dailyReq = daysLeft > 0 ? Math.round((remaining / daysLeft) * 100) / 100 : remaining;

    let status = row[11] || "Active";
    if (current >= target) status = "Completed";
    else if (daysLeft < 0) status = "Overdue";

    goals.push({
      id: row[0],
      name: row[1],
      category: row[2],
      target_amount: target,
      current_amount: current,
      progress_percentage: progress,
      remaining_amount: remaining,
      deadline: Utilities.formatDate(deadlineDate, Session.getScriptTimeZone(), "yyyy-MM-dd"),
      days_remaining: daysLeft,
      daily_required: dailyReq,
      email_alerts: row[8] === "Yes" || row[8] === true || row[8] === 1,
      user_email: row[9],
      priority: row[10],
      status: status,
      purpose: row[12],
      created_at: row[13]
    });
  }

  return goals;
}

/**
 * Creates a new savings goal
 */
function createGoal(goalData) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(SHEETS_CONFIG.GOALS_TAB) || ss.insertSheet(SHEETS_CONFIG.GOALS_TAB);
  
  const id = Utilities.getUuid().substring(0, 8);
  const nowStr = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), "yyyy-MM-dd HH:mm:ss");
  const target = parseFloat(goalData.target_amount) || 0;
  const current = parseFloat(goalData.initial_savings) || 0;
  const remaining = Math.max(0, target - current);
  const progress = target > 0 ? Math.round((current / target) * 1000) / 10 : 0;
  const status = current >= target ? "Completed" : "Active";

  sheet.appendRow([
    id,
    goalData.name,
    goalData.category || "General",
    target,
    current,
    progress + "%",
    remaining,
    goalData.deadline,
    goalData.email_alerts ? "Yes" : "No",
    goalData.user_email || Session.getActiveUser().getEmail(),
    goalData.priority || "Medium",
    status,
    goalData.purpose || "",
    nowStr,
    nowStr
  ]);

  if (current > 0) {
    addDeposit(id, goalData.name, current, "Initial savings deposit");
  }

  return { success: true, goal_id: id };
}

/**
 * Record a deposit / contribution towards a goal
 */
function addDeposit(goalId, goalName, amount, note) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const depSheet = ss.getSheetByName(SHEETS_CONFIG.DEPOSITS_TAB);
  const nowStr = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), "yyyy-MM-dd");
  
  depSheet.appendRow([
    Utilities.getUuid().substring(0, 6),
    goalId,
    goalName,
    parseFloat(amount),
    note || "Deposit",
    nowStr
  ]);

  // Update current amount in Goals Sheet
  const goalsSheet = ss.getSheetByName(SHEETS_CONFIG.GOALS_TAB);
  const data = goalsSheet.getDataRange().getValues();
  for (let i = 1; i < data.length; i++) {
    if (data[i][0] == goalId) {
      const current = (parseFloat(data[i][4]) || 0) + parseFloat(amount);
      const target = parseFloat(data[i][3]) || 0;
      const progress = target > 0 ? Math.round((current / target) * 1000) / 10 : 0;
      const remaining = Math.max(0, target - current);
      const status = current >= target ? "Completed" : data[i][11];

      goalsSheet.getRange(i + 1, 5).setValue(current);
      goalsSheet.getRange(i + 1, 6).setValue(progress + "%");
      goalsSheet.getRange(i + 1, 7).setValue(remaining);
      goalsSheet.getRange(i + 1, 12).setValue(status);
      goalsSheet.getRange(i + 1, 15).setValue(Utilities.formatDate(new Date(), Session.getScriptTimeZone(), "yyyy-MM-dd HH:mm:ss"));
      break;
    }
  }

  return { success: true };
}

/**
 * Deletes a goal and its associated records
 */
function deleteGoal(goalId) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const goalsSheet = ss.getSheetByName(SHEETS_CONFIG.GOALS_TAB);
  const data = goalsSheet.getDataRange().getValues();
  
  for (let i = 1; i < data.length; i++) {
    if (data[i][0] == goalId) {
      goalsSheet.deleteRow(i + 1);
      return { success: true };
    }
  }
  return { success: false, message: "Goal not found" };
}

/**
 * AI Financial Recommendation via Groq API (LLaMA 3.3-70B Versatile)
 */
function getAIRecommendation(goal) {
  const apiKey = SCRIPT_PROP.getProperty("GROQ_API_KEY");

  const target = parseFloat(goal.target_amount) || 0;
  const current = parseFloat(goal.current_amount) || 0;
  const remaining = Math.max(0, target - current);
  const days = goal.days_remaining || 30;
  const daily = days > 0 ? Math.round((remaining / days) * 100) / 100 : remaining;
  const weekly = Math.round(daily * 7 * 100) / 100;

  // Fallback heuristic if API Key is not yet set
  if (!apiKey) {
    return {
      goal_name: goal.name,
      recommendation: `You have saved $${current.toLocaleString()} out of $${target.toLocaleString()} (${goal.progress_percentage}%). To hit your target in ${days} days, save $${daily}/day or $${weekly}/week.`,
      daily_saving_target: daily,
      weekly_saving_target: weekly,
      feasibility_score: daily < 50 ? 90 : 65,
      strategies: [
        `Automate weekly deposits of $${weekly} directly into savings.`,
        "Cut non-essential discretionary subscriptions.",
        "Allocate future windfalls or cashbacks directly to this goal."
      ],
      motivational_quote: "Small daily savings compound into monumental financial freedom.",
      source: "SaveIQ Local Heuristic Engine (Configure GROQ_API_KEY in Script Properties for LLaMA 3.3-70B)"
    };
  }

  const prompt = `
You are the AI Financial Advisor in SaveIQ. Analyze this goal and return strictly a valid JSON object:
Goal: ${goal.name} (${goal.category})
Target: $${target} | Current: $${current} | Remaining: $${remaining}
Days Left: ${days} | Daily Required: $${daily}
Purpose: ${goal.purpose || 'None'}

Return JSON schema:
{
  "recommendation": "Executive 2-sentence advice",
  "daily_saving_target": ${daily},
  "weekly_saving_target": ${weekly},
  "feasibility_score": 85,
  "strategies": ["strategy 1", "strategy 2", "strategy 3"],
  "motivational_quote": "inspiring financial quote"
}
`;

  try {
    const response = UrlFetchApp.fetch("https://api.groq.com/openai/v1/chat/completions", {
      method: "post",
      headers: {
        "Authorization": "Bearer " + apiKey,
        "Content-Type": "application/json"
      },
      payload: JSON.stringify({
        model: SHEETS_CONFIG.DEFAULT_MODEL,
        messages: [
          { role: "system", content: "You are SaveIQ FinTech advisor. Output valid JSON only." },
          { role: "user", content: prompt }
        ],
        temperature: 0.3,
        response_format: { type: "json_object" }
      }),
      muteHttpExceptions: true
    });

    const json = JSON.parse(response.getContentText());
    const aiData = JSON.parse(json.choices[0].message.content);
    aiData.goal_name = goal.name;
    aiData.source = "Groq LLaMA 3.3-70B Versatile";
    return aiData;
  } catch (err) {
    return {
      goal_name: goal.name,
      recommendation: `Pacing calculation: Target $${daily}/day to finish on schedule.`,
      daily_saving_target: daily,
      weekly_saving_target: weekly,
      feasibility_score: 75,
      strategies: ["Automate weekly savings transfers", "Track daily budget"],
      motivational_quote: "Consistency is the key to financial security.",
      source: "SaveIQ Fallback Advisor"
    };
  }
}

/**
 * Automated Daily Financial Audit & Gmail Alert Notification Engine
 */
function auditDeadlinesAndSendAlerts() {
  const goals = getGoals();
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const alertsSheet = ss.getSheetByName(SHEETS_CONFIG.ALERTS_TAB);
  const nowStr = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), "yyyy-MM-dd HH:mm:ss");

  let alertsSent = 0;

  goals.forEach(goal => {
    if (!goal.email_alerts) return;

    let alertType = null;
    let message = "";

    if (goal.status === "Completed") {
      // Completed, no urgent warning needed
    } else if (goal.days_remaining < 0) {
      alertType = "OVERDUE";
      message = `Your goal "${goal.name}" passed its deadline. Remaining gap: $${goal.remaining_amount.toLocaleString()}.`;
    } else if (goal.days_remaining <= 7) {
      alertType = "URGENT";
      message = `URGENT: "${goal.name}" deadline is in ${goal.days_remaining} days! Save $${goal.daily_required}/day to complete.`;
    } else if (goal.days_remaining <= 30 && goal.progress_percentage < 50) {
      alertType = "WARNING";
      message = `Goal pace alert: "${goal.name}" is at ${goal.progress_percentage}% with ${goal.days_remaining} days left.`;
    }

    if (alertType) {
      // Record alert
      alertsSheet.appendRow([
        Utilities.getUuid().substring(0, 6),
        goal.id,
        goal.name,
        alertType,
        message,
        goal.user_email,
        nowStr
      ]);

      // Send Gmail Alert
      try {
        GmailApp.sendEmail(
          goal.user_email,
          `SaveIQ Financial Alert: ${goal.name} [${alertType}]`,
          message,
          {
            htmlBody: `
              <div style="font-family: Arial, sans-serif; max-width: 600px; padding: 20px; border: 1px solid #e2e8f0; border-radius: 8px;">
                <h3 style="color: #4f46e5;">SaveIQ Savings Alert: ${alertType}</h3>
                <p>${message}</p>
                <p><b>Goal:</b> ${goal.name}<br/><b>Target:</b> $${goal.target_amount}<br/><b>Current:</b> $${goal.current_amount} (${goal.progress_percentage}%)</p>
                <p style="font-size: 12px; color: #64748b;">Powered by SaveIQ Google Apps Script Automation.</p>
              </div>
            `
          }
        );
        alertsSent++;
      } catch (e) {
        Logger.log("Email dispatch skipped or simulated: " + e.message);
      }
    }
  });

  return { success: true, alertsSent: alertsSent, totalAudited: goals.length };
}

/**
 * Sets up the Daily Time-Driven Trigger for Automated Audits
 */
function setupDailyAuditTrigger() {
  // Clear existing triggers to avoid duplicates
  const triggers = ScriptApp.getProjectTriggers();
  triggers.forEach(t => {
    if (t.getHandlerFunction() === "auditDeadlinesAndSendAlerts") {
      ScriptApp.deleteTrigger(t);
    }
  });

  // Create new daily trigger at 8:00 AM
  ScriptApp.newTrigger("auditDeadlinesAndSendAlerts")
    .timeBased()
    .atHour(8)
    .everyDays(1)
    .create();

  return "Daily 8:00 AM Financial Audit trigger scheduled successfully!";
}
