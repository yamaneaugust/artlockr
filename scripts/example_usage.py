"""
Example usage of the ArtLockr API.
Demonstrates the basic workflow for copyright detection.
"""
import requests
import json
from pathlib import Path

# API base URL
BASE_URL = "http://localhost:8000/api/v1"


def upload_artwork(image_path: str, title: str, description: str = ""):
    """Upload an original artwork"""
    print(f"\n📤 Uploading artwork: {title}")

    url = f"{BASE_URL}/upload-artwork"

    with open(image_path, 'rb') as f:
        files = {'file': f}
        data = {
            'title': title,
            'description': description
        }
        response = requests.post(url, files=files, data=data)

    if response.status_code == 200:
        result = response.json()
        print(f"✅ Upload successful!")
        print(f"   Artwork ID: {result['id']}")
        print(f"   File path: {result['file_path']}")
        print(f"   Features extracted: {result['feature_extracted']}")
        return result['id']
    else:
        print(f"❌ Upload failed: {response.text}")
        return None


def detect_copyright(artwork_id: int, threshold: float = 0.85, top_k: int = 10):
    """Detect copyright infringement for an artwork"""
    print(f"\n🔍 Detecting copyright infringement for artwork ID: {artwork_id}")

    url = f"{BASE_URL}/detect-copyright/{artwork_id}"
    params = {
        'threshold': threshold,
        'top_k': top_k
    }
    response = requests.post(url, params=params)

    if response.status_code == 200:
        result = response.json()
        print(f"✅ Detection complete!")
        print(f"   Detection ID: {result['detection_id']}")
        print(f"   Matches found: {result['matches_found']}")
        print(f"   Threshold used: {result['threshold']}")

        if result['matches_found'] > 0:
            print(f"\n   🚨 Potential copyright infringements:")
            for i, match in enumerate(result['matches'], 1):
                print(f"      {i}. {match['image_name']}")
                print(f"         Similarity: {match['similarity_score']}%")
                print(f"         Path: {match['image_path']}")
        else:
            print(f"\n   ✅ No copyright infringements detected!")

        return result
    else:
        print(f"❌ Detection failed: {response.text}")
        return None


def block_organization(org_name: str, org_domain: str, reason: str):
    """Block an organization from accessing artwork"""
    print(f"\n🚫 Blocking organization: {org_name}")

    url = f"{BASE_URL}/api-gate/block"
    data = {
        'organization_name': org_name,
        'organization_domain': org_domain,
        'reason': reason
    }
    response = requests.post(url, json=data)

    if response.status_code == 200:
        result = response.json()
        print(f"✅ Organization blocked successfully!")
        print(f"   Block ID: {result['id']}")
        print(f"   Organization: {result['organization_name']}")
        return result
    else:
        print(f"❌ Blocking failed: {response.text}")
        return None


def get_statistics():
    """Get copyright protection statistics"""
    print(f"\n📊 Fetching statistics...")

    url = f"{BASE_URL}/statistics"
    response = requests.get(url)

    if response.status_code == 200:
        stats = response.json()
        print(f"✅ Statistics:")
        print(f"   Total artworks: {stats['total_artworks']}")
        print(f"   Total detections: {stats['total_detections']}")
        print(f"   Total matches found: {stats['total_matches_found']}")
        print(f"   Blocked organizations: {stats['blocked_organizations']}")
        return stats
    else:
        print(f"❌ Failed to get statistics: {response.text}")
        return None


def main():
    """Main example workflow"""
    print("=" * 60)
    print("ArtLockr - Copyright Detection Example")
    print("=" * 60)

    # Example 1: Upload artwork
    # Note: Replace with actual image path
    artwork_path = "data/uploads/sample_artwork.jpg"

    if Path(artwork_path).exists():
        artwork_id = upload_artwork(
            image_path=artwork_path,
            title="My Original Artwork",
            description="This is my original digital painting"
        )

        if artwork_id:
            # Example 2: Detect copyright infringement
            detect_copyright(
                artwork_id=artwork_id,
                threshold=0.85,
                top_k=5
            )

            # Example 3: Block an organization
            block_organization(
                org_name="UnauthorizedAI Corp",
                org_domain="unauthorizedai.com",
                reason="Found my artwork in their training dataset without permission"
            )

    # Example 4: Get statistics
    get_statistics()

    print("\n" + "=" * 60)
    print("Example complete!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to the API server.")
        print("   Make sure the server is running at http://localhost:8000")
    except Exception as e:
        print(f"\n❌ Error: {e}")
