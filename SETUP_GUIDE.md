# Telegram Lead Gen Bot - Setup Guide

Follow these steps to securely configure your API keys and connect the system to Modal.

## 1. Get a Telegram Bot Token
1. Open Telegram and search for the `@BotFather` account.
2. Send the message `/newbot` to start the creation process.
3. Follow the prompts to give your bot a name and a username.
4. BotFather will reply with an API Token (looks like `1234567890:ABCDefghIJKLmnopQRSTuvwxYZ`).
5. Copy this token.

## 2. Get a Gemini API Key
1. Go to Google AI Studio: https://aistudio.google.com/
2. Click on "Get API key" in the left sidebar.
3. Create an API key in a new or existing project.
4. Copy the API key (usually starts with `AIza...`).

## 3. Create an Airtable Database and Token
### Setting up the Database Schema
1. Create a new Airtable Base.
2. Ensure the first table has the following exact column names with their respective types:
   - `Name` (Single line text)
   - `Service` (Single line text)
   - `Address` (Single line text)
   - `Website` (URL or Single line text)
   - `Email` (Email or Single line text)
   - `Rating` (Number - Decimal)
   - `Date Created` (Date)
   - `Status` (Single select with options like "Lead", "Contacted", or just a Single line text)
3. Get the **Base ID**: Look at the URL of your base: `https://airtable.com/appXXXXXXXXXXXXXX/tblYYYYYYYYYYYYYY`. The Base ID is the part starting with `app`.
4. The **Table Name** is the exact case-sensitive name of the table tab you are working in (e.g., `Table 1` or `Leads`).

### Getting the API Key (Personal Access Token)
1. Go to Airtable Developer Hub: https://airtable.com/create/tokens
2. Click "Create new token".
3. Name it "Telegram Bot".
4. Add scopes: `data.records:read` and `data.records:write`.
5. Add access: Allow it to access the Base you just created.
6. Click "Create token" and copy it (starts with `pat...`).

## 4. Storing Secrets in Modal
We will securely pass these keys to Modal without writing them in code.

Run this exact command in your terminal, replacing the dummy values with your real keys. **Make sure to run this as one single continuous line, do not copy the line breaks**:

```bash
modal secret create bot-secrets TELEGRAM_BOT_TOKEN="your_telegram_token" GEMINI_API_KEY="your_gemini_key" AIRTABLE_API_KEY="your_airtable_token" AIRTABLE_BASE_ID="your_base_id" AIRTABLE_TABLE_NAME="your_table_name"
```

## 5. Deploying and Setting the Webhook
1. Deploy the Modal application:
   ```bash
   modal deploy execution/modal_bot.py
   ```
2. Modal will output a URL that looks like `https://YOUR_WORKSPACE_NAME--telegram-lead-gen-bot-telegram-webhook.modal.run`.
3. Set your Telegram bot's webhook to point to this URL. You can do this simply by pasting this URL in your browser:
   `https://api.telegram.org/bot<YOUR_TELEGRAM_BOT_TOKEN>/setWebhook?url=<YOUR_MODAL_WEBHOOK_URL>`
   *(Make sure to replace the `<YOUR_TELEGRAM_BOT_TOKEN>` and `<YOUR_MODAL_WEBHOOK_URL>` with your actual token and Modal URL).*
4. You should see a JSON response in the browser: `{"ok":true,"result":true,"description":"Webhook was set"}`.

You are fully deployed!
