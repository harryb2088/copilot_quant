# Deployment Guide for Copilot Quant Platform

This guide provides a quick reference for deploying the Copilot Quant Platform to Vercel.

## Quick Start

### Prerequisites
- ✅ [Vercel account](https://vercel.com/signup)
- ✅ [Vercel CLI](https://vercel.com/docs/cli) installed: `npm install -g vercel`
- ✅ GitHub repository access
- ✅ Authentication credentials ready

### 3-Step Deployment

#### Step 1: Deploy to Vercel
```bash
# Login to Vercel
vercel login

# Deploy the application
vercel

# Follow the prompts and confirm settings
```

#### Step 2: Configure Environment Variables
```bash
# Add authentication credentials
vercel env add AUTH_EMAIL      # e.g., admin@example.com
vercel env add AUTH_PASSWORD   # Your secure password
vercel env add AUTH_NAME       # e.g., "Admin User"

# Select Production, Preview, and Development for each
```

#### Step 3: Redeploy with Environment Variables
```bash
# Production deployment with environment variables
vercel --prod
```

## Post-Deployment

### Update README
After deployment, update the `README.md` file:

1. Replace `YOUR-DEPLOYMENT-URL` with your actual Vercel URL (e.g., `https://copilot-quant.vercel.app`)
2. Update deployment badge link at the top of README
3. Commit and push the changes

### Verify Deployment
- [ ] Visit your Vercel deployment URL
- [ ] Confirm Streamlit app loads
- [ ] Test authentication login
- [ ] Verify all pages work correctly
- [ ] Share URL with team

## Environment Variables

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `AUTH_EMAIL` | Login email/username | `admin@copilotquant.com` | Yes |
| `AUTH_PASSWORD` | Login password | `SecurePassword123!` | Yes |
| `AUTH_NAME` | Display name | `Admin User` | Yes |

## Alternative Deployment via Dashboard

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click "Add New Project"
3. Import `harryb2088/copilot_quant` repository
4. Configure:
   - Framework: `Other`
   - Build Command: (leave empty)
   - Output Directory: (leave empty)
5. Add environment variables:
   - `AUTH_EMAIL`
   - `AUTH_PASSWORD`
   - `AUTH_NAME`
6. Click "Deploy"

## Managing Environment Variables

### Update Password
```bash
# Remove old password
vercel env rm AUTH_PASSWORD

# Add new password
vercel env add AUTH_PASSWORD

# Redeploy
vercel --prod
```

### View Current Variables
```bash
# List all environment variables
vercel env ls
```

### Remove All Auth (Make Public)
```bash
# Remove authentication
vercel env rm AUTH_EMAIL
vercel env rm AUTH_PASSWORD
vercel env rm AUTH_NAME

# Redeploy
vercel --prod
```

## Troubleshooting

### Deployment Fails
```bash
# Check deployment logs
vercel logs <deployment-url>

# View build logs in Vercel Dashboard
# Go to: Dashboard → Project → Deployments → Click failed deployment
```

### Authentication Not Working
- Verify variable names are exact: `AUTH_EMAIL`, `AUTH_PASSWORD`, `AUTH_NAME`
- Ensure you redeployed after setting variables: `vercel --prod`
- Check deployment logs for authentication errors

### App Loads Slowly
- First load after deployment may take longer (cold start)
- Subsequent loads should be faster
- Consider custom domain for improved caching

## Custom Domain (Optional)

### Add Custom Domain
```bash
# Add domain via CLI
vercel domains add yourdomain.com

# Or use Vercel Dashboard:
# Project Settings → Domains → Add
```

### Configure DNS
1. Add DNS records as shown in Vercel
2. Wait for propagation (can take up to 48 hours)
3. Vercel automatically provisions SSL certificate

## Monitoring

### Check Deployment Status
```bash
# List recent deployments
vercel ls

# View deployment details
vercel inspect <deployment-url>
```

### View Logs
```bash
# Stream real-time logs
vercel logs <deployment-url> --follow

# View recent logs
vercel logs <deployment-url>
```

## Security Best Practices

1. **Strong Password**: Use a secure password (12+ characters, mixed case, numbers, symbols)
2. **Credential Management**: Store credentials in a password manager
3. **Team Access**: Share credentials securely (never via email/Slack)
4. **Regular Updates**: Rotate passwords periodically
5. **Environment Separation**: Use different credentials for production/preview/development

## Support

- 📖 [Full README](README.md#️-cloud-deployment-on-vercel)
- 🌐 [Vercel Documentation](https://vercel.com/docs)
- 📚 [Streamlit Documentation](https://docs.streamlit.io)
- 🐛 [Report Issues](https://github.com/harryb2088/copilot_quant/issues)

## Quick Commands Reference

```bash
# Deploy to production
vercel --prod

# Deploy to preview
vercel

# Add environment variable
vercel env add <VAR_NAME>

# Remove environment variable
vercel env rm <VAR_NAME>

# List environment variables
vercel env ls

# View logs
vercel logs <deployment-url>

# List deployments
vercel ls

# Remove deployment
vercel rm <deployment-name>
```

---

**Ready to deploy?** Follow the [3-Step Deployment](#3-step-deployment) above to get started!
