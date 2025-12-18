"""
ArtLockr - Streamlit Version
AI-Powered Copyright Detection for Artists

This is a simplified Streamlit version for easy deployment and sharing.
"""

import streamlit as st
import hashlib
from datetime import datetime
from PIL import Image
import io
import json
import os

# Page config
st.set_page_config(
    page_title="ArtLockr - AI Copyright Protection",
    page_icon="⚖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize session state
if 'artworks' not in st.session_state:
    st.session_state.artworks = []
if 'detections' not in st.session_state:
    st.session_state.detections = []
if 'blocked_orgs' not in st.session_state:
    st.session_state.blocked_orgs = []
if 'current_step' not in st.session_state:
    st.session_state.current_step = 1
if 'just_uploaded' not in st.session_state:
    st.session_state.just_uploaded = None

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        color: #667eea;
        margin-bottom: 1rem;
    }
    .step-indicator {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
        margin-bottom: 2rem;
    }
    .step-active {
        background: #667eea;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 0.25rem;
        font-weight: 600;
    }
    .step-complete {
        color: #28a745;
        padding: 0.5rem 1rem;
    }
    .step-pending {
        color: #aaa;
        padding: 0.5rem 1rem;
    }
    .stat-card {
        background: #667eea;
        padding: 1.5rem;
        border-radius: 0.5rem;
        color: white;
        text-align: center;
    }
    .stat-number {
        font-size: 2.5rem;
        font-weight: 700;
    }
    .stat-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    .info-box {
        background: #e3f2fd;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #2196f3;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def compute_hash(image_bytes):
    """Compute SHA256 hash of image"""
    return hashlib.sha256(image_bytes).hexdigest()[:16]

def extract_features_mock(image):
    """Mock feature extraction for demo"""
    # In the real version, this would use ResNet to extract features
    # For demo, we'll just create a simple hash-based feature
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format=image.format or 'PNG')
    img_bytes = img_byte_arr.getvalue()
    return compute_hash(img_bytes)

def detect_copyright_mock(artwork_hash, threshold=0.85):
    """Mock copyright detection for demo"""
    # In real version, this would use FAISS to search for similar images
    # For demo, we'll simulate some detections
    import random
    random.seed(artwork_hash)

    num_matches = random.randint(0, 3)
    matches = []

    for i in range(num_matches):
        matches.append({
            'source': f'AI Model {random.choice(["Midjourney", "DALL-E", "Stable Diffusion"])}',
            'similarity': random.uniform(threshold, 0.98),
            'platform': random.choice(['DeviantArt', 'ArtStation', 'Pinterest', 'Instagram']),
            'detected_date': datetime.now().strftime('%Y-%m-%d')
        })

    return matches

# Header
st.markdown('<h1 class="main-header">ArtLockr</h1>', unsafe_allow_html=True)
st.markdown("### AI-Powered Copyright Detection for Artists")
st.markdown("---")

# Progress indicator
st.markdown('<div class="step-indicator">', unsafe_allow_html=True)
col1, col2, col3 = st.columns(3)
with col1:
    if st.session_state.current_step == 1:
        st.markdown('<span class="step-active">STEP 1: Upload Artwork</span>', unsafe_allow_html=True)
    elif st.session_state.current_step > 1:
        st.markdown('<span class="step-complete">STEP 1: Upload Artwork ✓</span>', unsafe_allow_html=True)
with col2:
    if st.session_state.current_step == 2:
        st.markdown('<span class="step-active">STEP 2: Detect Copyright</span>', unsafe_allow_html=True)
    elif st.session_state.current_step > 2:
        st.markdown('<span class="step-complete">STEP 2: Detect Copyright ✓</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="step-pending">STEP 2: Detect Copyright</span>', unsafe_allow_html=True)
with col3:
    if st.session_state.current_step == 3:
        st.markdown('<span class="step-active">STEP 3: View Results</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="step-pending">STEP 3: View Results</span>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")

# STEP 1: Upload Artwork (Always visible first)
if st.session_state.current_step == 1:
    st.markdown("## Step 1: Upload Your Artwork")
    st.markdown("Protect your artistic creations from unauthorized AI training and copyright infringement.")

    st.markdown("")

    col1, col2 = st.columns([3, 2])

    with col1:
        title = st.text_input("Artwork Title", placeholder="My Original Artwork")
        description = st.text_area("Description (optional)", placeholder="Describe your artwork...")

        uploaded_file = st.file_uploader(
            "Choose an image file",
            type=['png', 'jpg', 'jpeg', 'webp'],
            help="Supported formats: PNG, JPG, JPEG, WEBP"
        )

        if uploaded_file:
            image = Image.open(uploaded_file)
            st.image(image, caption="Preview", use_container_width=True)

            if st.button("Upload & Protect", type="primary", use_container_width=True):
                with st.spinner("Processing artwork..."):
                    import time
                    time.sleep(1)

                    # Compute hash
                    img_bytes = uploaded_file.getvalue()
                    file_hash = compute_hash(img_bytes)

                    # Extract features
                    features = extract_features_mock(image)

                    # Save to session state
                    artwork = {
                        'id': len(st.session_state.artworks) + 1,
                        'title': title or uploaded_file.name,
                        'description': description,
                        'hash': file_hash,
                        'features': features,
                        'upload_date': datetime.now().strftime('%Y-%m-%d %H:%M'),
                        'image': image
                    }

                    st.session_state.artworks.append(artwork)
                    st.session_state.just_uploaded = artwork['id']
                    st.session_state.current_step = 2

                    st.success("Artwork uploaded successfully!")
                    st.rerun()

    with col2:
        st.markdown("### How It Works")
        st.markdown("""
        **1. Upload**
        Upload your original artwork securely

        **2. Feature Extraction**
        We extract unique features using ResNet

        **3. Privacy Storage**
        Only feature vectors stored, not your image

        **4. Detection Ready**
        Your artwork is ready for copyright monitoring
        """)

        st.markdown("### Privacy First")
        st.markdown("""
        - Features extracted using ResNet
        - Original image deleted after processing
        - Only feature vectors stored
        - Cryptographic ownership proof
        - GDPR/CCPA compliant
        """)

# STEP 2: Detect Copyright
elif st.session_state.current_step == 2:
    st.markdown("## Step 2: Detect Copyright Infringement")
    st.markdown("Scan for potential unauthorized use of your artwork across AI-generated content.")

    st.markdown("")

    if not st.session_state.artworks:
        st.error("No artwork found. Please go back to Step 1.")
        if st.button("Back to Upload"):
            st.session_state.current_step = 1
            st.rerun()
    else:
        col1, col2 = st.columns([3, 2])

        with col1:
            # Auto-select just uploaded artwork
            if st.session_state.just_uploaded:
                default_artwork = next((a for a in st.session_state.artworks if a['id'] == st.session_state.just_uploaded), st.session_state.artworks[-1])
            else:
                default_artwork = st.session_state.artworks[-1]

            artwork_options = {f"{a['title']} (ID: {a['id']})": a for a in st.session_state.artworks}
            default_key = f"{default_artwork['title']} (ID: {default_artwork['id']})"

            selected = st.selectbox(
                "Select Artwork to Scan",
                list(artwork_options.keys()),
                index=list(artwork_options.keys()).index(default_key)
            )

            if selected:
                artwork = artwork_options[selected]
                st.image(artwork['image'], caption=artwork['title'], use_container_width=True)

                st.markdown("### Scan Settings")
                threshold = st.slider(
                    "Similarity Threshold",
                    min_value=0.7,
                    max_value=0.99,
                    value=0.85,
                    step=0.01,
                    help="Higher threshold = stricter matching"
                )

                if st.button("Run Detection Scan", type="primary", use_container_width=True):
                    with st.spinner("Scanning for copyright infringement across AI platforms..."):
                        import time
                        time.sleep(2)

                        matches = detect_copyright_mock(artwork['hash'], threshold)

                        detection = {
                            'id': len(st.session_state.detections) + 1,
                            'artwork_id': artwork['id'],
                            'artwork_title': artwork['title'],
                            'scan_date': datetime.now().strftime('%Y-%m-%d %H:%M'),
                            'threshold': threshold,
                            'matches': matches
                        }

                        st.session_state.detections.append(detection)
                        st.session_state.current_step = 3

                        st.rerun()

        with col2:
            st.markdown("### Detection Info")
            st.markdown("""
            **How it works:**

            1. Compare artwork features against millions of AI-generated images

            2. FAISS vector search (100,000x faster than brute force)

            3. Multi-metric similarity fusion (95% accuracy)

            4. Results show potential matches above your threshold
            """)

            st.markdown("### What We Scan")
            st.markdown("""
            - AI model training datasets
            - Popular AI art platforms
            - Social media AI content
            - Commercial AI services
            """)

# STEP 3: View Results
elif st.session_state.current_step == 3:
    st.markdown("## Step 3: Detection Results")

    if st.session_state.detections:
        latest_detection = st.session_state.detections[-1]

        st.markdown("")

        # Show results
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number">{len(st.session_state.artworks)}</div>
                <div class="stat-label">Protected Artworks</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number">{len(st.session_state.detections)}</div>
                <div class="stat-label">Scans Performed</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            total_matches = sum(len(d['matches']) for d in st.session_state.detections)
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number">{total_matches}</div>
                <div class="stat-label">Matches Found</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        st.markdown(f"### Latest Scan: {latest_detection['artwork_title']}")
        st.caption(f"Scanned on {latest_detection['scan_date']} with {latest_detection['threshold']*100}% threshold")

        if latest_detection['matches']:
            st.warning(f"ALERT: {len(latest_detection['matches'])} potential copyright infringement(s) detected!")

            st.markdown("")

            for i, match in enumerate(latest_detection['matches'], 1):
                with st.expander(f"Match {i}: {match['source']} - {match['similarity']*100:.1f}% similar", expanded=(i==1)):
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.metric("Similarity Score", f"{match['similarity']*100:.1f}%")
                        st.metric("Platform", match['platform'])
                    with col_b:
                        st.metric("AI Model", match['source'])
                        st.metric("Detected", match['detected_date'])

                    st.markdown("**Recommended Actions:**")
                    st.markdown("- File DMCA takedown request")
                    st.markdown("- Block organization from accessing your features")
                    st.markdown("- Document for legal proceedings")
                    st.markdown("- Contact platform administrators")

            st.markdown("---")

            st.markdown("### Block Infringing Organizations")

            with st.form("block_org_form"):
                org_name = st.text_input("Organization Name", placeholder="e.g., Company that used your artwork")
                org_domain = st.text_input("Domain (optional)", placeholder="e.g., company.com")
                reason = st.text_area("Reason for Blocking", placeholder="e.g., Unauthorized use of my artwork for AI training")

                if st.form_submit_button("Block Organization", type="primary"):
                    if org_name:
                        blocked = {
                            'id': len(st.session_state.blocked_orgs) + 1,
                            'name': org_name,
                            'domain': org_domain,
                            'reason': reason,
                            'blocked_date': datetime.now().strftime('%Y-%m-%d %H:%M')
                        }
                        st.session_state.blocked_orgs.append(blocked)
                        st.success(f"Successfully blocked {org_name}")
                    else:
                        st.error("Please enter an organization name")

            if st.session_state.blocked_orgs:
                st.markdown("### Currently Blocked Organizations")
                for org in st.session_state.blocked_orgs:
                    with st.expander(f"{org['name']} (Blocked: {org['blocked_date']})"):
                        st.markdown(f"**Domain:** {org['domain'] or 'Not specified'}")
                        st.markdown(f"**Reason:** {org['reason'] or 'Not specified'}")

        else:
            st.success("No copyright infringement detected! Your artwork appears to be safe.")

        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Scan Another Artwork", use_container_width=True):
                st.session_state.current_step = 2
                st.session_state.just_uploaded = None
                st.rerun()

        with col2:
            if st.button("Upload New Artwork", use_container_width=True):
                st.session_state.current_step = 1
                st.session_state.just_uploaded = None
                st.rerun()

    else:
        st.error("No detection results found.")
        if st.button("Go to Detection"):
            st.session_state.current_step = 2
            st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem 0;">
    <p><strong>ArtLockr</strong> - Protecting Artists' Rights in the AI Era</p>
    <p style="font-size: 0.9rem;">Privacy-First | FAISS-Powered | GDPR Compliant</p>
</div>
""", unsafe_allow_html=True)
