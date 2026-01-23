# 🚀 Deployment Guide: Kerala Jersey Backend (Vercel)

This project is configured to be deployed as a Serverless Function on **Vercel**. Follow these steps to ensure a smooth deployment.

---

## 🛠 1. Prerequisites
- A **Vercel** account (linked to your GitHub).
- An **Appwrite** project with a Database and Collection ready.
- All environment variables from your `.env` file.

---

## 🔑 2. Environment Variables (CRITICAL)
Vercel cannot read your local `.env` file. You **MUST** manually add these variables in the Vercel Dashboard.

1. Go to your project on [Vercel](https://vercel.com).
2. Navigate to **Settings** > **Environment Variables**.
3. Add the following keys with their values from your local `.env`:
   - `APPWRITE_ENDPOINT`
   - `APPWRITE_PROJECT_ID`
   - `APPWRITE_API_KEY`
   - `APPWRITE_DATABASE_ID`
   - `APPWRITE_COLLECTION_ID`
   - `APPWRITE_BUCKET_ID`

---

## 📦 3. Deployment Methods

### Method A: GitHub (Recommended)
1. Push your code to your GitHub repository:
   ```bash
   git add .
   git commit -m "deploy"
   git push origin main
   ```
2. In Vercel, click **"Add New"** > **"Project"** and import the repository.
3. Vercel will automatically detect the `vercel.json` and deploy.

### Method B: Vercel CLI
1. Install the CLI: `npm install -g vercel`
2. Run `vercel` in the root folder.
3. Follow the prompts to link the project.
4. Run `vercel --prod` for final deployment.

---

## ⚡ 4. Important Files
- **`vercel.json`**: Tells Vercel how to handle the FastAPI request.
- **`requirements.txt`**: List of Python packages Vercel must install.
- **`runtime.txt`**: Forces Vercel to use a stable Python version (e.g., `python-3.12`).
- **`.vercelignore`**: Prevents unnecessary files (like `.venv` or `.env`) from being uploaded.

---

## ❓ 5. Troubleshooting

### "ModuleNotFoundError: No module named 'pydantic_core'"
- This usually happens if the Python version is incompatible or experimental.
- **Fix**: Ensure `runtime.txt` is set to `python-3.12` and `requires-python` in `pyproject.toml` is `>=3.12`.

### "Internal Server Error (500)"
- Check the **Function Logs** in the Vercel Dashboard.
- Usually caused by missing Environment Variables or incorrect Appwrite credentials.

### Deployment "Processing" forever
- If you change `requirements.txt`, Vercel takes longer to install new packages.
- If it fails, try **Redeploying** and select **"Redeploy without Build Cache"**.

---

## 🔗 6. Endpoints
Once deployed, your API will be available at:
- `https://your-project-url.vercel.app/`
- Interactive Docs: `https://your-project-url.vercel.app/docs`
- Health Check: `https://your-project-url.vercel.app/health`
