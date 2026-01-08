# Google Cloud Run Deployment Guide - Complete Beginner Tutorial

This guide provides **exact step-by-step instructions** for deploying the API Integration Assistant to Google Cloud Run using Docker. Written for complete beginners with no prior experience.

---

## 📋 Table of Contents

1. [Cost Information](#cost-information)
2. [Prerequisites](#prerequisites)
3. [Step 1: Install Required Software](#step-1-install-required-software)
4. [Step 2: Create Google Cloud Account](#step-2-create-google-cloud-account)
5. [Step 3: Set Up Google Cloud Project](#step-3-set-up-google-cloud-project)
6. [Step 4: Install and Configure Google Cloud CLI](#step-4-install-and-configure-google-cloud-cli)
7. [Step 5: Test Docker Build Locally](#step-5-test-docker-build-locally)
8. [Step 6: Push Docker Image to Google Cloud](#step-6-push-docker-image-to-google-cloud)
9. [Step 7: Deploy to Cloud Run](#step-7-deploy-to-cloud-run)
10. [Step 8: Configure Environment Variables](#step-8-configure-environment-variables)
11. [Step 9: Test Your Deployment](#step-9-test-your-deployment)
12. [Step 10: Set Up Custom Domain (Optional)](#step-10-set-up-custom-domain-optional)
13. [Troubleshooting](#troubleshooting)
14. [Managing Costs](#managing-costs)

---

## 💰 Cost Information

### Free Tier (No Credit Card Required Initially)
Google Cloud offers **$300 in free credits** for 90 days for new accounts. Additionally, Cloud Run has a generous **always-free tier**:

- **2 million requests per month** - FREE
- **360,000 GB-seconds of memory** - FREE
- **180,000 vCPU-seconds of compute time** - FREE
- **1 GB network egress from North America per month** - FREE

### Expected Costs After Free Tier

For **light usage** (100-1,000 requests/day):
- **$0-5 per month** - Likely stays within free tier

For **moderate usage** (5,000-10,000 requests/day):
- **$10-30 per month** - Minimal costs beyond free tier

**Note:** The application uses ChromaDB which requires persistent storage. This will add storage costs:
- **Cloud Storage** (for vector database): ~$0.02/GB/month
- For a 10 GB database: **~$0.20/month**

**Total minimum cost estimate: $0-5/month** for personal/development use.

---

## 📌 Prerequisites

Before starting, make sure you have:

1. ✅ A Google account (Gmail account)
2. ✅ A computer with internet connection (Windows, macOS, or Linux)
3. ✅ Administrator/sudo access on your computer
4. ✅ Your project code downloaded (this repository)

---

## Step 1: Install Required Software

### A. Install Docker Desktop

Docker is the tool that packages your application into a container.

#### **For Windows:**

1. **Download Docker Desktop:**
   - Go to: https://www.docker.com/products/docker-desktop
   - Click "Download for Windows"
   - Download the installer (Docker Desktop Installer.exe)

2. **Install Docker Desktop:**
   - Double-click the downloaded `.exe` file
   - Follow the installation wizard
   - Check "Use WSL 2 instead of Hyper-V" if prompted
   - Click "Ok" and wait for installation to complete
   - Restart your computer when prompted

3. **Verify Installation:**
   - Open Command Prompt (press `Windows Key + R`, type `cmd`, press Enter)
   - Type the following command and press Enter:
   ```cmd
   docker --version
   ```
   - You should see output like: `Docker version 24.x.x`

#### **For macOS:**

1. **Download Docker Desktop:**
   - Go to: https://www.docker.com/products/docker-desktop
   - Click "Download for Mac"
   - Choose the version for your Mac:
     - **Intel chip**: Download "Mac with Intel chip"
     - **Apple Silicon (M1/M2/M3)**: Download "Mac with Apple chip"

2. **Install Docker Desktop:**
   - Open the downloaded `.dmg` file
   - Drag the Docker icon to the Applications folder
   - Open Docker from Applications
   - Approve the security prompts
   - Wait for Docker to start (you'll see a whale icon in the menu bar)

3. **Verify Installation:**
   - Open Terminal (press `Command + Space`, type "Terminal", press Enter)
   - Type:
   ```bash
   docker --version
   ```
   - You should see output like: `Docker version 24.x.x`

#### **For Linux (Ubuntu/Debian):**

1. **Open Terminal** (Ctrl + Alt + T)

2. **Update package list:**
   ```bash
   sudo apt-get update
   ```

3. **Install Docker:**
   ```bash
   sudo apt-get install -y docker.io
   ```

4. **Start Docker service:**
   ```bash
   sudo systemctl start docker
   sudo systemctl enable docker
   ```

5. **Add your user to docker group** (to run docker without sudo):
   ```bash
   sudo usermod -aG docker $USER
   ```

6. **Log out and log back in** for group changes to take effect

7. **Verify Installation:**
   ```bash
   docker --version
   ```

---

## Step 2: Create Google Cloud Account

1. **Go to Google Cloud Console:**
   - Open your web browser
   - Visit: https://console.cloud.google.com

2. **Sign in with Google Account:**
   - Click "Get started for free" or "Sign in"
   - Use your existing Gmail account or create a new one

3. **Set up billing (Free Credits):**
   - Google will ask you to set up billing to get the $300 free credit
   - Click "Activate" to start the free trial
   - Enter your country
   - Accept the Terms of Service
   - Click "Continue"

4. **Enter Payment Information:**
   - **Don't worry:** Google won't charge you without permission
   - Enter your credit/debit card information
   - This is only for identity verification
   - You'll get **$300 free credits** for 90 days
   - After free credits expire, you must manually upgrade to be charged

5. **Click "Start my free trial"**

6. **Complete the survey** (optional) and click "Done"

**✅ Checkpoint:** You should now be at the Google Cloud Console dashboard.

---

## Step 3: Set Up Google Cloud Project

1. **Create a New Project:**
   - At the top of Google Cloud Console, click the **project dropdown** (next to "Google Cloud")
   - Click **"New Project"**
   - Enter a project name: `api-assistant-production` (or any name you prefer)
   - Leave organization as "No organization"
   - Click **"Create"**
   - Wait 10-20 seconds for the project to be created

2. **Select Your Project:**
   - Click the project dropdown again
   - Select your newly created project: `api-assistant-production`
   - The project name should now appear in the top bar

3. **Enable Required APIs:**

   You need to enable several Google Cloud services:

   a. **Enable Cloud Run API:**
   - In the search bar at the top, type: `Cloud Run API`
   - Click on "Cloud Run API" in the results
   - Click the blue **"Enable"** button
   - Wait for it to enable (10-30 seconds)

   b. **Enable Artifact Registry API:**
   - Click the back button or search again
   - In the search bar, type: `Artifact Registry API`
   - Click on "Artifact Registry API"
   - Click **"Enable"**
   - Wait for it to enable

   c. **Enable Cloud Build API:**
   - Click the hamburger menu (☰) in the top-left corner
   - Scroll down to **"APIs & Services"**
   - Click **"Library"**
   - In the Library search box, type: `Cloud Build`
   - Look for **"Cloud Build API"** with the Google Cloud icon
   - Click on it and then click **"Enable"**

**✅ Checkpoint:** You now have a project with Cloud Run, Artifact Registry, and Cloud Build enabled.

---

## Step 4: Install and Configure Google Cloud CLI

The Google Cloud CLI (`gcloud`) is a command-line tool to interact with Google Cloud.

### A. Install Google Cloud CLI

#### **For Windows:**

1. **Download the installer:**
   - Go to: https://cloud.google.com/sdk/docs/install
   - Click "Download the Google Cloud CLI installer for Windows"
   - Download `GoogleCloudSDKInstaller.exe`

2. **Run the installer:**
   - Double-click the downloaded file
   - Follow the installation wizard
   - Check "Run 'gcloud init'" at the end
   - Click "Finish"

3. **A new window will open** running `gcloud init`

#### **For macOS:**

1. **Download the installer:**
   - Go to: https://cloud.google.com/sdk/docs/install
   - Download the package for your Mac (Intel or Apple Silicon)
   - Example: `google-cloud-cli-darwin-arm.tar.gz` for M1/M2/M3 Macs

2. **Extract and install:**
   - Open Terminal
   - Navigate to your Downloads folder:
   ```bash
   cd ~/Downloads
   ```
   - Extract the archive:
   ```bash
   tar -xf google-cloud-cli-*.tar.gz
   ```
   - Run the install script:
   ```bash
   ./google-cloud-sdk/install.sh
   ```
   - Follow the prompts, press Enter to accept defaults

3. **Initialize gcloud:**
   ```bash
   ./google-cloud-sdk/bin/gcloud init
   ```

#### **For Linux:**

1. **Download and install:**
   ```bash
   curl https://sdk.cloud.google.com | bash
   ```

2. **Restart your shell:**
   ```bash
   exec -l $SHELL
   ```

3. **Initialize gcloud:**
   ```bash
   gcloud init
   ```

### B. Configure Google Cloud CLI

When `gcloud init` runs, follow these steps:

1. **Log in:**
   - You'll see: "You must log in to continue. Would you like to log in (Y/n)?"
   - Type: `Y` and press Enter
   - A web browser will open
   - Sign in with your Google account
   - Click "Allow" to grant permissions
   - You'll see "You are now authenticated"
   - Close the browser window

2. **Select your project:**
   - You'll see a list of your projects
   - Find the number next to your project (e.g., `[1] api-assistant-production`)
   - Type that number and press Enter

3. **Select a default region:**
   - You'll see: "Do you want to configure a default Compute Region and Zone? (Y/n)?"
   - Type: `Y` and press Enter
   - You'll see a list of regions
   - **Choose a region close to your users** for best performance:
     - **US East Coast**: Type `13` for `us-east1`
     - **US West Coast**: Type `27` for `us-west1`
     - **Europe**: Type `10` for `europe-west1`
     - **Asia**: Type `3` for `asia-east1`
   - Press Enter

4. **Verify configuration:**
   ```bash
   gcloud config list
   ```
   - You should see your project, account, and region

**✅ Checkpoint:** Run `gcloud --version` - you should see the version number.

---

## Step 5: Test Docker Build Locally

Before deploying to Cloud Run, let's make sure your Docker image builds correctly.

### A. Open Terminal/Command Prompt

- **Windows:** Open Command Prompt or PowerShell
- **macOS/Linux:** Open Terminal

### B. Navigate to Your Project Directory

```bash
cd /path/to/Api-Assistant
```

**Replace `/path/to/Api-Assistant`** with your actual project path. For example:
- **Windows:** `cd C:\Users\YourName\Documents\Api-Assistant`
- **macOS:** `cd ~/Documents/Api-Assistant`
- **Linux:** `cd ~/Api-Assistant`

### C. Build the Docker Image

Run this command:

```bash
docker build -t api-assistant:test .
```

**What this does:**
- `docker build`: Builds a Docker image
- `-t api-assistant:test`: Names (tags) the image as "api-assistant:test"
- `.`: Uses the current directory (where Dockerfile is located)

**Expected output:**
- You'll see many lines of output
- It will download Python, install dependencies, etc.
- This takes 5-10 minutes the first time
- **Final line should say:** `Successfully built [image-id]` and `Successfully tagged api-assistant:test`

**If you see errors:**
- Make sure Docker Desktop is running (you should see the whale icon)
- Make sure you're in the correct directory (run `ls` or `dir` and verify you see `Dockerfile`)
- Check the [Troubleshooting](#troubleshooting) section

### D. Test the Image Locally

Now let's run the image to make sure it works:

1. **Start the container:**
   ```bash
   docker run -p 8000:8000 -e SECRET_KEY=test-secret-key-12345 api-assistant:test
   ```

   **What this does:**
   - `docker run`: Runs a container from the image
   - `-p 8000:8000`: Maps port 8000 from container to your computer
   - `-e SECRET_KEY=...`: Sets a test secret key
   - `api-assistant:test`: The image name we just built

2. **Wait for the server to start:**
   - You should see output like:
   ```
   INFO:     Started server process [1]
   INFO:     Waiting for application startup.
   INFO:     Application startup complete.
   INFO:     Uvicorn running on http://0.0.0.0:8000
   ```

3. **Test the health endpoint:**
   - Open a **new** terminal/command prompt window
   - Run:
   ```bash
   curl http://localhost:8000/health
   ```
   - **Or** open your web browser and go to: `http://localhost:8000/health`
   - You should see: `{"status":"healthy"}`

4. **Test the API docs:**
   - Open your browser to: `http://localhost:8000/docs`
   - You should see the FastAPI interactive documentation (Swagger UI)

5. **Stop the container:**
   - Go back to the terminal running Docker
   - Press `Ctrl + C` to stop the container

**✅ Checkpoint:** Your Docker image builds and runs successfully locally.

---

## Step 6: Push Docker Image to Google Cloud

Now we'll push your Docker image to Google's container registry so Cloud Run can use it.

### A. Create an Artifact Registry Repository

Artifact Registry is where you'll store your Docker images in Google Cloud.

1. **Run this command** (replace `REGION` with your region, e.g., `us-east1`):
   ```bash
   gcloud artifacts repositories create api-assistant-repo \
       --repository-format=docker \
       --location=us-east1 \
       --description="Docker repository for API Assistant"
   ```

   **Choose your region:**
   - Use the same region you selected during `gcloud init`
   - Common options: `us-east1`, `us-west1`, `europe-west1`, `asia-east1`

2. **Wait for confirmation:**
   - You should see: `Created repository [api-assistant-repo]`

**✅ Checkpoint:** Run `gcloud artifacts repositories list` - you should see your repository.

### B. Configure Docker to Authenticate with Google Cloud

Tell Docker to use your Google Cloud credentials:

```bash
gcloud auth configure-docker us-east1-docker.pkg.dev
```

**Replace `us-east1`** with your chosen region if different.

- You'll see: "Do you want to continue (Y/n)?" - Type `Y` and press Enter
- You should see: "Docker configuration file updated"

### C. Tag Your Docker Image for Google Cloud

Give your Docker image a name that Google Cloud understands:

```bash
docker tag api-assistant:test us-east1-docker.pkg.dev/PROJECT_ID/api-assistant-repo/api-assistant:v1
```

**⚠️ IMPORTANT:** Replace the following:
- **`us-east1`** - Your region
- **`PROJECT_ID`** - Your Google Cloud project ID

**To find your PROJECT_ID:**
```bash
gcloud config get-value project
```
- Copy the output (e.g., `api-assistant-production-123456`)

**Full example command:**
```bash
docker tag api-assistant:test us-east1-docker.pkg.dev/api-assistant-production-123456/api-assistant-repo/api-assistant:v1
```

### D. Push the Image to Google Cloud

Upload your Docker image:

```bash
docker push us-east1-docker.pkg.dev/PROJECT_ID/api-assistant-repo/api-assistant:v1
```

**⚠️ Replace `PROJECT_ID` and `us-east1`** with your values (same as above).

**What happens:**
- Docker will upload your image layer by layer
- This takes 5-15 minutes depending on your internet speed
- You'll see progress bars for each layer
- **Final output:** `v1: digest: sha256:... size: ...`

**✅ Checkpoint:** Your image is now in Google Cloud Artifact Registry!

Verify with:
```bash
gcloud artifacts docker images list us-east1-docker.pkg.dev/PROJECT_ID/api-assistant-repo
```

---

## Step 7: Deploy to Cloud Run

Now we'll deploy your Docker image to Cloud Run!

### A. Deploy the Service

Run this command (replace `PROJECT_ID` and `us-east1` with your values):

```bash
gcloud run deploy api-assistant \
    --image us-east1-docker.pkg.dev/PROJECT_ID/api-assistant-repo/api-assistant:v1 \
    --platform managed \
    --region us-east1 \
    --port 8000 \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --max-instances 10 \
    --set-env-vars "SECRET_KEY=CHANGE_THIS_TO_A_RANDOM_SECRET_12345"
```

**What each option means:**

- `--image`: The Docker image to deploy (from Artifact Registry)
- `--platform managed`: Use fully managed Cloud Run (not GKE)
- `--region us-east1`: Deploy to US East Coast (change to your region)
- `--port 8000`: The port your application listens on (FastAPI default)
- `--allow-unauthenticated`: Allow public access (no Google login required)
- `--memory 2Gi`: Allocate 2 GB of RAM (ChromaDB needs memory)
- `--cpu 2`: Allocate 2 CPU cores
- `--timeout 300`: Allow requests up to 5 minutes (for large document processing)
- `--max-instances 10`: Scale up to 10 containers if needed
- `--set-env-vars`: Set environment variables (we'll add more in next step)

**Questions you'll be asked:**

1. **"Service name (api-assistant):"** - Press Enter to accept
2. **"API [run.googleapis.com] not enabled"** - Type `Y` to enable
3. **"Allow unauthenticated invocations to [api-assistant]?"** - Type `Y`

**Wait for deployment:**
- This takes 1-3 minutes
- You'll see: "Deploying container to Cloud Run service..."
- **Final output:** `Service [api-assistant] revision [api-assistant-00001-xxx] has been deployed and is serving 100 percent of traffic.`
- **You'll see a URL** like: `https://api-assistant-xxxxx-uc.a.run.app`

**✅ Checkpoint:** Copy the URL! This is your live API endpoint.

### B. Test the Deployment

1. **Test the health endpoint:**
   ```bash
   curl https://YOUR_CLOUD_RUN_URL/health
   ```
   - **Replace `YOUR_CLOUD_RUN_URL`** with the URL from the previous step
   - You should see: `{"status":"healthy"}`

2. **Open the API docs:**
   - Open your browser to: `https://YOUR_CLOUD_RUN_URL/docs`
   - You should see the FastAPI Swagger UI

**If the health check fails:**
- Wait 30-60 seconds and try again (container may still be starting)
- Check the [Troubleshooting](#troubleshooting) section

---

## Step 8: Configure Environment Variables

Your application needs several environment variables for full functionality. Let's add them.

### A. Generate a Strong Secret Key

Run this in your terminal to generate a random secret key:

**For macOS/Linux:**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

**For Windows (PowerShell):**
```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Copy the output** - you'll use this as your `SECRET_KEY`.

### B. Set Environment Variables

Run this command with your values:

```bash
gcloud run services update api-assistant \
    --region us-east1 \
    --update-env-vars "\
SECRET_KEY=YOUR_GENERATED_SECRET_KEY,\
GROQ_API_KEY=YOUR_GROQ_API_KEY,\
FRONTEND_URL=https://your-frontend-domain.com,\
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2,\
LLM_PROVIDER=groq,\
GROQ_MODEL=mixtral-8x7b-32768,\
ENABLE_QUERY_EXPANSION=true,\
LOG_LEVEL=INFO"
```

**⚠️ Replace the following:**

1. **`YOUR_GENERATED_SECRET_KEY`** - The secret key you just generated
2. **`YOUR_GROQ_API_KEY`** - Your Groq API key (get free key at https://console.groq.com)
3. **`https://your-frontend-domain.com`** - Your Next.js frontend URL (if deployed), or remove this line if testing backend only
4. **`us-east1`** - Your region

**Optional environment variables** you can add:

- `OLLAMA_BASE_URL` - If using Ollama instead of Groq
- `CHROMA_DB_PATH=/app/data/chroma_db` - Default path for vector database
- `MAX_UPLOAD_SIZE_MB=50` - Maximum file upload size
- `CORS_ALLOWED_ORIGINS=*` - For development (use specific domain in production)

**What happens:**
- Cloud Run will redeploy your service with new environment variables
- This takes 1-2 minutes
- You'll see: "Deploying..."
- **Final output:** Service updated successfully

### C. Verify Environment Variables

Check that your variables are set:

```bash
gcloud run services describe api-assistant --region us-east1 --format="value(spec.template.spec.containers[0].env)"
```

You should see your environment variables listed.

**✅ Checkpoint:** Your service is now configured with all required environment variables.

---

## Step 9: Test Your Deployment

Let's do a comprehensive test of your deployed application.

### A. Test the Health Endpoint

```bash
curl https://YOUR_CLOUD_RUN_URL/health
```

**Expected response:**
```json
{"status":"healthy"}
```

### B. Test the Search Endpoint

```bash
curl -X POST "https://YOUR_CLOUD_RUN_URL/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "authentication",
    "n_results": 5,
    "mode": "hybrid",
    "use_query_expansion": false,
    "min_score": 0.0
  }'
```

**Expected response:**
```json
{
  "results": [],
  "query": "authentication",
  "total_results": 0,
  "mode": "hybrid"
}
```
(Empty results are normal if you haven't uploaded any documents yet)

### C. Test Document Upload

1. **Create a test file:**
   - Create a file named `test.txt` with some content:
   ```
   This is a test API documentation.
   Authentication: Use Bearer tokens.
   Endpoint: POST /api/v1/auth
   ```

2. **Upload the document:**
   ```bash
   curl -X POST "https://YOUR_CLOUD_RUN_URL/api/v1/documents/upload/text" \
     -F "file=@test.txt" \
     -F "metadata={}"
   ```

   **Expected response:**
   ```json
   {
     "status": "success",
     "chunks_created": 1,
     "document_id": "..."
   }
   ```

3. **Search again:**
   ```bash
   curl -X POST "https://YOUR_CLOUD_RUN_URL/api/v1/search" \
     -H "Content-Type: application/json" \
     -d '{"query": "authentication", "n_results": 5}'
   ```

   **Now you should see results!**

### D. Test the API Documentation UI

Open your browser to:
```
https://YOUR_CLOUD_RUN_URL/docs
```

You should see the FastAPI Swagger UI with all available endpoints.

**✅ Checkpoint:** Your API is fully deployed and working!

---

## Step 10: Set Up Custom Domain (Optional)

If you want to use your own domain instead of the `*.run.app` URL:

### A. Verify Domain Ownership

1. **Go to Cloud Run in Console:**
   - Visit: https://console.cloud.google.com/run
   - Click on your service: `api-assistant`

2. **Add a custom domain:**
   - Click the "MANAGE CUSTOM DOMAINS" tab
   - Click "+ ADD MAPPING"
   - Select your service: `api-assistant`
   - Enter your domain: e.g., `api.yourdomain.com`
   - Click "Continue"

3. **Verify domain:**
   - Google will provide DNS records to add
   - Add these records to your domain registrar (GoDaddy, Namecheap, etc.)
   - Wait for verification (5-30 minutes)

### B. Update DNS

Google will provide:
- An `A` record
- An `AAAA` record
- Or a `CNAME` record

Add these to your domain's DNS settings.

**✅ Checkpoint:** After DNS propagation (can take up to 48 hours), your API will be available at your custom domain.

---

## 🔧 Troubleshooting

### Issue: Docker build fails with "permission denied"

**Solution (Linux):**
```bash
sudo usermod -aG docker $USER
```
Then log out and log back in.

### Issue: `gcloud: command not found`

**Solution:**
- Close and reopen your terminal
- Or run: `source ~/.bashrc` (Linux/Mac) or restart Command Prompt (Windows)

### Issue: Cloud Run health check fails

**Possible causes:**

1. **Port mismatch:**
   - Cloud Run expects port 8080 by default
   - Add to your deploy command: `--port 8000`
   - Or set environment variable: `PORT=8000`

2. **Health endpoint not responding:**
   - Check logs: `gcloud run services logs read api-assistant --region us-east1`
   - Verify `/health` endpoint exists in your code

3. **Container takes too long to start:**
   - Increase timeout: `--timeout 300`
   - Check memory allocation: `--memory 2Gi`

### Issue: "Permission denied" when pushing to Artifact Registry

**Solution:**
```bash
gcloud auth configure-docker us-east1-docker.pkg.dev
```

### Issue: Out of memory errors

**Solution:**
Increase memory allocation:
```bash
gcloud run services update api-assistant \
    --region us-east1 \
    --memory 4Gi
```

**Note:** This increases costs but may be necessary for ChromaDB.

### Issue: Slow response times

**Possible causes:**

1. **Cold starts:** First request after idle period is slow
   - **Solution:** Set minimum instances: `--min-instances 1`
   - **Note:** This increases costs (you'll pay for 1 instance always running)

2. **Insufficient CPU:**
   - **Solution:** Increase CPU: `--cpu 4`

### Issue: Data not persisting between deployments

**Explanation:**
Cloud Run containers are **stateless** - they don't preserve data between restarts.

**Solution:**
You need to set up persistent storage for ChromaDB. See below.

---

## 💾 Setting Up Persistent Storage (ChromaDB)

**Problem:** Cloud Run containers are stateless. When a container restarts, all data in ChromaDB is lost.

**Solution Options:**

### Option 1: Cloud Storage (Recommended for Development)

Cloud Run doesn't directly support persistent volumes like Railway. You need to:

1. **Use Cloud Storage for ChromaDB:**
   - Modify your code to store ChromaDB data in Google Cloud Storage
   - This requires code changes to use `chromadb-cloud` or custom storage backend

2. **Or use Cloud SQL for PostgreSQL:**
   - Use ChromaDB with PostgreSQL backend instead of local files
   - More complex but production-ready

### Option 2: Cloud Filestore (Paid, More Expensive)

1. **Create a Filestore instance:**
   ```bash
   gcloud filestore instances create chroma-storage \
       --zone=us-east1-b \
       --tier=BASIC_HDD \
       --file-share=name="chromadb",capacity=1TB \
       --network=name="default"
   ```

2. **Mount in Cloud Run:**
   - Currently in beta, requires VPC connector
   - More complex setup

### Option 3: External Vector Database (Recommended for Production)

Use a managed vector database instead of ChromaDB:

- **Pinecone** (has free tier)
- **Weaviate Cloud** (has free tier)
- **Qdrant Cloud** (has free tier)

**This requires code changes** but provides better scalability and persistence.

### Recommended Approach

For **testing/development:**
- Accept that data will reset on each deployment
- Upload test documents after each deployment

For **production:**
- Migrate to Pinecone (free tier: 1M vectors, ~$0/month)
- Or use Cloud SQL with ChromaDB PostgreSQL backend

**Would you like help setting up one of these options?**

---

## 💵 Managing Costs

### Monitor Your Usage

1. **View current costs:**
   - Go to: https://console.cloud.google.com/billing
   - Click on your billing account
   - View "Reports" to see costs

2. **Set up budget alerts:**
   - Click "Budgets & alerts"
   - Click "CREATE BUDGET"
   - Set budget amount: e.g., $10/month
   - Set alert threshold: 50%, 90%, 100%
   - Enter your email
   - Click "FINISH"

**You'll get email alerts** when you approach your budget.

### Reduce Costs

1. **Delete unused services:**
   ```bash
   gcloud run services delete api-assistant --region us-east1
   ```

2. **Reduce memory/CPU:**
   ```bash
   gcloud run services update api-assistant \
       --region us-east1 \
       --memory 1Gi \
       --cpu 1
   ```

3. **Reduce max instances:**
   ```bash
   gcloud run services update api-assistant \
       --region us-east1 \
       --max-instances 3
   ```

4. **Set minimum instances to 0:**
   ```bash
   gcloud run services update api-assistant \
       --region us-east1 \
       --min-instances 0
   ```
   (Containers will shut down when idle - slower first request but free when not in use)

### Estimated Monthly Costs

**Scenario 1: Personal use (100 requests/day)**
- Cloud Run: $0 (within free tier)
- Artifact Registry: $0 (within free tier)
- **Total: $0/month**

**Scenario 2: Light production (1,000 requests/day)**
- Cloud Run: $0-5
- Artifact Registry: $0.10
- Cloud Storage (if used): $0.20
- **Total: $0.30-5.30/month**

**Scenario 3: Moderate production (10,000 requests/day, min-instances=1)**
- Cloud Run: $15-30
- Artifact Registry: $0.10
- Cloud Storage: $0.50
- **Total: $15.60-30.60/month**

---

## 🎉 Congratulations!

You've successfully deployed your API Integration Assistant to Google Cloud Run!

### Your Deployment URLs:

- **API Base URL:** `https://api-assistant-xxxxx-uc.a.run.app`
- **API Documentation:** `https://api-assistant-xxxxx-uc.a.run.app/docs`
- **Health Check:** `https://api-assistant-xxxxx-uc.a.run.app/health`

### Next Steps:

1. **Deploy your Next.js frontend** (to Vercel, Netlify, or Cloud Run)
2. **Set up persistent storage** for ChromaDB (see options above)
3. **Configure custom domain** (optional)
4. **Set up monitoring and logging** in Google Cloud Console
5. **Enable HTTPS** (automatically provided by Cloud Run)

### Useful Commands:

**View logs:**
```bash
gcloud run services logs read api-assistant --region us-east1 --limit 50
```

**Update the service:**
```bash
# After making code changes, rebuild and push:
docker build -t api-assistant:v2 .
docker tag api-assistant:v2 us-east1-docker.pkg.dev/PROJECT_ID/api-assistant-repo/api-assistant:v2
docker push us-east1-docker.pkg.dev/PROJECT_ID/api-assistant-repo/api-assistant:v2

# Deploy the new version:
gcloud run deploy api-assistant \
    --image us-east1-docker.pkg.dev/PROJECT_ID/api-assistant-repo/api-assistant:v2 \
    --region us-east1
```

**Delete the service:**
```bash
gcloud run services delete api-assistant --region us-east1
```

---

## 📚 Additional Resources

- **Cloud Run Documentation:** https://cloud.google.com/run/docs
- **Google Cloud Free Tier:** https://cloud.google.com/free
- **Docker Documentation:** https://docs.docker.com
- **FastAPI Documentation:** https://fastapi.tiangolo.com
- **Troubleshooting Cloud Run:** https://cloud.google.com/run/docs/troubleshooting

---

## ❓ Need Help?

If you encounter issues not covered in this guide:

1. **Check the logs:**
   ```bash
   gcloud run services logs read api-assistant --region us-east1
   ```

2. **Check Cloud Run status:**
   ```bash
   gcloud run services describe api-assistant --region us-east1
   ```

3. **Visit Google Cloud Console:**
   - https://console.cloud.google.com/run
   - Click on your service to see metrics and errors

4. **Google Cloud Support:**
   - Free tier includes community support
   - Visit: https://cloud.google.com/support

---

**Good luck with your deployment! 🚀**
