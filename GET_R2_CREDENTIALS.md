# 🔐 GET YOUR R2 API CREDENTIALS - 2 MINUTE GUIDE

## ✅ What We Already Have:
- Account ID: `31277d24f8b9b001c73c1a3e2866fd0e`
- Bucket Name: `mysite`
- S3 Endpoint: `https://31277d24f8b9b001c73c1a3e2866fd0e.r2.cloudflarestorage.com`

## ⚠️ What You Need to Get (2 minutes):
- R2 Access Key ID (17 characters)
- R2 Secret Access Key (40 characters)

---

## 📋 STEP-BY-STEP:

### 1. Open R2 API Tokens Page
**Click this exact link:**
```
https://dash.cloudflare.com/31277d24f8b9b001c73c1a3e2866fd0e/r2/api-tokens
```

### 2. Create API Token
1. Click **"Create API token"** button (blue button, top right)
2. Fill in the form:
   - **Token name:** `elitewealthcapital-production`
   - **Permissions:** Select **"Object Read & Write"**
   - **TTL (optional):** Leave as **"Forever"** or set to 1 year
3. Click **"Create API Token"**

### 3. COPY YOUR CREDENTIALS IMMEDIATELY!
⚠️ **CRITICAL:** The Secret Access Key is shown **ONLY ONCE!**

You'll see a screen with:
```
Access Key ID:        abc123xyz789defgh  (17 chars - looks like this)
Secret Access Key:    very-long-40-character-secret-key-here  (40 chars)
```

**Copy BOTH values now!**

### 4. Update render.yaml
Replace in your `render.yaml` file (lines 68-69):

**BEFORE:**
```yaml
- key: R2_ACCESS_KEY_ID
  value: YOUR_R2_ACCESS_KEY_HERE
- key: R2_SECRET_ACCESS_KEY
  value: YOUR_R2_SECRET_KEY_HERE
```

**AFTER:**
```yaml
- key: R2_ACCESS_KEY_ID
  value: [PASTE YOUR ACCESS KEY ID HERE]
- key: R2_SECRET_ACCESS_KEY
  value: [PASTE YOUR SECRET ACCESS KEY HERE]
```

### 5. Save and Verify
Check `render.yaml` lines 65-75 should look like:
```yaml
# Cloudflare R2 Storage (Media Files - Uploads, KYC, Receipts)
# Account: 31277d24f8b9b001c73c1a3e2866fd0e (bthailand998@gmail.com)
- key: R2_ACCESS_KEY_ID
  value: abc123xyz789defgh  # ✅ YOUR ACTUAL KEY
- key: R2_SECRET_ACCESS_KEY
  value: very-long-40-character-secret  # ✅ YOUR ACTUAL SECRET
- key: R2_BUCKET_NAME
  value: mysite  # ✅ CORRECT
- key: R2_ENDPOINT_URL
  value: https://31277d24f8b9b001c73c1a3e2866fd0e.r2.cloudflarestorage.com  # ✅ CORRECT
- key: R2_CUSTOM_DOMAIN
  value: ""
```

---

## 🚀 AFTER YOU UPDATE render.yaml:

### Deploy to Render:
```bash
cd "C:\Users\HP PC\Documents\MY-SITE"
git add render.yaml
git commit -m "🔧 Add R2 credentials for production storage"
git push origin main
```

Render will auto-deploy in ~3-5 minutes!

---

## ✅ VERIFICATION CHECKLIST:

After deployment:
1. [ ] Upload a profile picture → Should go to R2
2. [ ] Check Cloudflare R2 dashboard → File should appear in `mysite` bucket
3. [ ] Download a PDF receipt → Should work
4. [ ] Check Render logs → Should see "Using R2 storage backend"

---

## 🆘 TROUBLESHOOTING:

**If you see "Access Denied" error:**
- Check Access Key ID is exactly 17 characters
- Check Secret Access Key is exactly 40 characters
- No extra spaces or quotes in render.yaml

**If files still go to Cloudinary:**
- Check DEBUG=False in render.yaml (line 23)
- Check R2_ACCESS_KEY_ID is set (not empty)

**Lost your Secret Access Key?**
- Delete the old token
- Create a new one
- Update render.yaml with new credentials

---

## 📞 READY?

1. ✅ Open: https://dash.cloudflare.com/31277d24f8b9b001c73c1a3e2866fd0e/r2/api-tokens
2. ✅ Create token
3. ✅ Copy credentials
4. ✅ Update render.yaml
5. ✅ Git push
6. ✅ Deploy!

**Let me know when you have the credentials and I'll help you deploy!** 🚀
