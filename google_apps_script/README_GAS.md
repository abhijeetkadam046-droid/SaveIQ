# SaveIQ – Google Apps Script & Google Sheets Deployment Guide

This guide describes how to deploy **SaveIQ** into your Google Workspace environment using Google Sheets, Google Apps Script, Gmail Services, and Groq AI (LLaMA 3.3-70B Versatile).

---

## 🚀 Quick Setup (3 Minutes)

### Step 1: Create a Google Spreadsheet
1. Open [Google Sheets](https://sheets.new) and create a new sheet named: `SaveIQ Financial Database`.
2. Click **Extensions** > **Apps Script**.

### Step 2: Paste the Apps Script Code
1. In the Apps Script Editor, rename the default file to `Code.gs` and replace its contents with the code from [`Code.gs`](file:///d:/RAMESHWAR/google_apps_script/Code.gs).
2. Click **+ (Add a file)** > **HTML**, name it `Index`, and paste the code from [`Index.html`](file:///d:/RAMESHWAR/google_apps_script/Index.html).
3. In Project Settings (gear icon), check **"Show 'appsscript.json' manifest file in editor"**, open `appsscript.json`, and replace with [`appsscript.json`](file:///d:/RAMESHWAR/google_apps_script/appsscript.json).

### Step 3: Configure Groq API Key
1. Go to **Project Settings** (gear icon on the left panel).
2. Scroll to **Script Properties** and click **Add script property**:
   - **Property:** `GROQ_API_KEY`
   - **Value:** *Your Groq API Key (starts with `gsk_...`)*
3. Click **Save script properties**.

### Step 4: Initialize Sheets & Scheduled Triggers
1. In the Apps Script Editor, select the function dropdown and run `initializeSheetDatabase`.
2. Grant Google permissions when prompted.
3. Select and run `setupDailyAuditTrigger` to activate automated 8:00 AM daily deadline audits and email alert dispatches.

### Step 5: Deploy as Live Web App
1. Click the blue **Deploy** button (top right) > **New deployment**.
2. Select type: **Web app**.
3. Configuration:
   - **Description:** `SaveIQ v2.0 Production`
   - **Execute as:** `Me (your email)`
   - **Who has access:** `Anyone` (or `Anyone within your organization`)
4. Click **Deploy** and copy your **Web app URL**.
5. Open the Web app URL in any browser or on mobile!
