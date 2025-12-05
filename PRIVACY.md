# ArtLockr Privacy & Security Features

## 🔒 Privacy-First Architecture

ArtLockr is built with artist trust as the foundation. We understand that artists are rightfully concerned about uploading their precious artwork to yet another platform. Here's how we protect your intellectual property:

## ✅ What We Do

### 1. **Feature-Only Storage (Default)**

**How it works:**
- You upload your artwork
- We extract a 2048-dimensional mathematical fingerprint (feature vector)
- **We immediately delete your original image**
- We store ONLY the feature vector

**Why this protects you:**
- Feature vectors cannot be reversed back into images
- We have zero access to your original artwork
- Impossible for us to use your art for AI training
- You keep the original, we only have a mathematical signature

### 2. **Cryptographic Proof of Ownership**

Every upload generates:
- **SHA-256 file hash**: Unique fingerprint of your file
- **Proof hash**: Cryptographic proof combining (file hash + artist ID + timestamp)
- **Verification certificate**: Publicly verifiable proof you uploaded first

**Use cases:**
- Prove you created artwork before someone else
- Evidence for DMCA takedown requests
- Legal documentation of copyright ownership
- Share proof without sharing the actual artwork

**Example certificate:**
```json
{
  "certificate_type": "ArtLockr Ownership Proof",
  "artwork_id": 123,
  "artist_id": 456,
  "upload_timestamp": "2025-01-15T10:30:00Z",
  "file_hash_sha256": "a3f5...",
  "proof_hash": "7b2c...",
  "verification_url": "https://artlockr.com/verify/7b2c..."
}
```

### 3. **Data Transparency Dashboard**

Access `/api/v1/privacy/my-data` to see:
- Exactly what data we have on you
- How many images stored vs deleted
- Your privacy settings
- Data retention schedule
- Complete audit trail

### 4. **Auto-Deletion Policies**

**Default settings:**
- Original images: Deleted immediately after feature extraction
- Feature vectors: Retained for 30 days (configurable)
- Scheduled auto-deletion of old data

**You control:**
- Retention period (1-365 days, or permanent with opt-in)
- Storage mode (features_only, encrypted, full)
- Auto-delete vs manual control

### 5. **GDPR/CCPA Compliance**

**Your Rights:**
- ✅ **Right to Access**: See all your data anytime (`/privacy/my-data`)
- ✅ **Right to Deletion**: Delete everything with one click (`/privacy/delete-all`)
- ✅ **Right to Portability**: Export all your data in JSON format
- ✅ **Right to Rectification**: Update your information anytime

**Our Commitments:**
- We will NEVER use your artwork for AI training
- We will NEVER sell or share your data
- We delete data when you request it
- We are transparent about what we collect

## 🚫 What We DON'T Do

- ❌ Store your original artwork (unless you explicitly choose "full" storage mode)
- ❌ Use your art to train AI models
- ❌ Share your data with third parties
- ❌ Sell access to your artwork
- ❌ Keep data indefinitely without consent
- ❌ Make it hard to delete your data

## 🔐 Security Features

### 1. Secure File Deletion

When deleting files, we:
1. Overwrite the file with zeros
2. Then permanently delete it
3. Prevents recovery even with forensic tools

### 2. Encrypted Communication

- All API communication over HTTPS
- Encryption in transit and at rest (when using encrypted mode)

### 3. Access Logging

Every access attempt is logged:
- Who accessed what
- When they accessed it
- Whether access was granted/denied
- IP address and user agent

View your access logs in the privacy dashboard.

## 📊 Storage Modes

### Features Only (Default, Recommended)
```
✅ Most Private
✅ Fastest
✅ Uses least storage
✅ Cannot be used for AI training
❌ Original image not recoverable
```

**Best for:** Maximum privacy, you keep originals locally

### Encrypted (Coming Soon)
```
✅ Very Private
✅ Original encrypted with your key
✅ We can't view/use your art
✅ You can decrypt with your key
⚠️  More complex to use
```

**Best for:** Privacy + ability to recover originals

### Full Storage
```
⚠️  Less Private
✅ Original image available
✅ Simpler workflow
❌ We have access to your art
❌ You must trust us not to misuse it
```

**Best for:** Testing, trusted deployments

**We recommend "Features Only" for maximum privacy.**

## 🛡️ Trust Verification

### How to verify we're privacy-first:

1. **Code is Open Source**: Review our code on GitHub
2. **Cryptographic Proofs**: We can't fake the math
3. **Public Verification**: Anyone can verify ownership proofs
4. **Transparency Reports**: See exactly what data we store
5. **Third-Party Audits**: (Planned) Independent security audits

### Questions We Expect (and Answer)

**Q: How do I know you actually delete my images?**
A: Check your privacy dashboard - it shows which images are deleted. You can also audit the code (it's open source).

**Q: Can you recover my original artwork from feature vectors?**
A: No. Mathematically impossible. Feature vectors are one-way transformations.

**Q: What if I don't trust you at all?**
A: Fair! Use client-side feature extraction (coming soon) - extract features in your browser, only upload the features. We never see your artwork.

**Q: Can I verify my ownership proof without your platform?**
A: Yes! Proof hashes are standard SHA-256. Anyone with the formula can verify: `SHA256(file_hash:artist_id:timestamp)`.

**Q: What happens if ArtLockr shuts down?**
A: You can export all your data (proofs, hashes, features) before shutdown. Cryptographic proofs remain valid forever.

## 📖 Privacy API Endpoints

### Upload with Privacy
```bash
POST /api/v1/upload-artwork-private
```
- Uploads artwork
- Extracts features
- Deletes original image
- Returns cryptographic proof

### View Your Data
```bash
GET /api/v1/privacy/my-data
```
- See all data we have on you
- GDPR/CCPA compliant
- Complete transparency

### Delete All Data
```bash
POST /api/v1/privacy/delete-all
```
- Permanently delete everything
- Includes files and database records
- Irreversible (by design)

### Verify Ownership Proof
```bash
GET /api/v1/privacy/verify-proof/{proof_hash}
```
- Public verification endpoint
- Anyone can verify proof
- No authentication needed
- Proves artwork ownership

## 🎯 Privacy Best Practices

### For Maximum Privacy:

1. **Use Features-Only Mode** (default)
2. **Keep originals locally** - don't rely on cloud storage
3. **Generate proofs for everything** - even if not uploading
4. **Review access logs monthly** - check who accessed your data
5. **Set short retention periods** - auto-delete old features
6. **Export proofs regularly** - don't rely solely on our platform

### Privacy Checklist:

- [ ] Storage mode set to "features_only"
- [ ] Auto-delete images enabled
- [ ] Data retention period configured (30 days recommended)
- [ ] Privacy consent acknowledged
- [ ] Cryptographic proofs generated
- [ ] Access logs reviewed
- [ ] Data export tested

## 🔍 Transparency Commitment

We commit to:

1. **Open Source Code**: Anyone can audit our privacy implementation
2. **Regular Audits**: Third-party security audits (planned)
3. **Transparency Reports**: Publish what data we collect
4. **No Dark Patterns**: Easy data export/deletion, no tricks
5. **Clear Language**: No confusing legalese
6. **User Control**: You decide what we store and for how long

## 📧 Privacy Questions?

If you have privacy concerns or questions:
- Review the code: [GitHub Repository]
- Check the docs: `/docs` endpoint
- Privacy dashboard: `/privacy/my-data`
- Open an issue: [GitHub Issues]

## 🏆 Privacy Certifications (Planned)

- [ ] SOC 2 Compliance
- [ ] ISO 27001 Certification
- [ ] Third-party Security Audit
- [ ] Privacy Shield Framework
- [ ] GDPR Adequacy Assessment

---

**Bottom Line**: We built ArtLockr to PROTECT artists, not exploit them. Privacy is not a feature - it's the foundation.

**Last Updated**: 2025-12-05
**Version**: 2.0 (Privacy-First)
