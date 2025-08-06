from flask import Flask, render_template, request, jsonify, send_file
import requests
import random
import os
from io import BytesIO
from bs4 import BeautifulSoup


app = Flask(__name__)


# KEYS TO ACCESS THE IMAGES
UNSPLASH_ACCESS_KEY = os.environ.get("UNSPLASH_ACCESS_KEY")
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")  


RANDOM_WALLPAPER_QUERIES = [
    'nature', 'abstract', 'space', 'city', 'ocean', 'mountain', 'sunset', 
    'forest', 'anime', 'cars', 'technology', 'art', 'landscape', 'minimalist',
    'dark', 'colorful', 'fantasy', 'architecture', 'flowers', 'animals'
]

def fetch_wallpaperflare_images(query, page=1):
    query = query.replace(' ', '+')
    url = f"https://www.wallpaperflare.com/search?wallpaper={query}&page={page}"
    headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "Referer": "https://www.google.com/"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"Failed to load WallpaperFlare page: {response.status_code}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        images = []

        for fig in soup.find_all("figure"):
            img = fig.find("img")
            if img and "data-src" in img.attrs:
                images.append(img["data-src"])

        return images
    except Exception as e:
        print(f"Error fetching images from WallpaperFlare: {e}")
        return []

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/explore")
def explore():
    return render_template("explore.html")

@app.route("/image_detail")
def image_detail():
    image_url = request.args.get("url")
    image_alt = request.args.get("alt", "Image")
    image_author = request.args.get("author", "Unknown")
    image_source = request.args.get("source", "Unknown")
    image_likes = request.args.get("likes", "0")

    return render_template(
        "image_detail.html",
        image_url=image_url,
        image_alt=image_alt,
        image_author=image_author,
        image_source=image_source,
        image_likes=image_likes
    )

@app.route("/download_image")
def download_image():
    image_url = request.args.get("url")
    filename = request.args.get("filename", "downloaded_image.jpg")

    if not image_url:
        return "No image URL provided", 400

    try:
        response = requests.get(image_url, stream=True, timeout=10)
        response.raise_for_status()

        content_type = response.headers.get('Content-Type', 'application/octet-stream')
        image_data = BytesIO(response.content)

        return send_file(
            image_data,
            mimetype=content_type,
            as_attachment=True,
            download_name=filename
        )
    except requests.exceptions.RequestException as e:
        print(f"Error fetching image for download: {e}")
        return f"Error downloading image: {e}", 500
    except Exception as e:
        print(f"An unexpected error occurred during download: {e}")
        return "An unexpected error occurred", 500

# New route to handle image likes
@app.route('/like_image', methods=['POST'])
def like_image():
    data = request.get_json()
    image_url = data.get('image_url')

    if not image_url:
        return jsonify({'success': False, 'message': 'No image URL provided'}), 400

    # Simulate liking an image. In a real application, you would:
    # 1. Store likes in a database associated with the image URL or ID.
    # 2. Increment the like count for that image.
    # 3. Retrieve the updated like count.
    
    # For now, we'll just return a dummy incremented count.
    # You might want to pass the current like count from the frontend
    # and increment it here, or fetch it from a dummy store.
    
    # Let's assume a base like count and increment it
    # This is not persistent across server restarts or for multiple users
    # For a real application, implement a database (e.g., Firestore)
    
    # Simulate a successful like
    current_likes = random.randint(100, 10000) # This will generate a new random number each time
    new_likes_count = current_likes + 1 

    return jsonify({'success': True, 'new_likes_count': new_likes_count})


@app.route("/images")
def fetch_images():
    query = request.args.get("query", "")
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))

    print(f"\n🔍 Fetching images - Query: '{query}', Page: {page}")
    
    all_images = []
    total_pages = 1
    api_results = {
        'unsplash': {'success': False, 'count': 0, 'error': None},
        'pexels': {'success': False, 'count': 0, 'error': None},
        'nekos': {'success': False, 'count': 0, 'error': None},
        'artic': {'success': False, 'count': 0, 'error': None}
    }
 
    if UNSPLASH_ACCESS_KEY and UNSPLASH_ACCESS_KEY != "your_unsplash_access_key_here": # Set your unsplash key env not set
        try:
            unsplash_params = {
                "page": page,
                "per_page": min(per_page // 4, 10),
                "client_id": UNSPLASH_ACCESS_KEY
            }
            
            if query:
                unsplash_params["query"] = query
                unsplash_url = "https://api.unsplash.com/search/photos"
            else:
                unsplash_url = "https://api.unsplash.com/photos"
                
            print(f"📡 Calling Unsplash API: {unsplash_url}")
            unsplash = requests.get(unsplash_url, params=unsplash_params, timeout=10)
            
            print(f"Unsplash response status: {unsplash.status_code}")
            
            if unsplash.ok:
                data = unsplash.json()
                results = data.get("results", []) if query else data
                total_pages = max(total_pages, data.get("total_pages", 1) if query else 50)
                
                for img in results[:per_page//4]:
                    all_images.append({
                        "url": img["urls"]["regular"],
                        "thumbnail": img["urls"]["small"],
                        "source": "unsplash",
                        "alt": img.get("alt_description", "Unsplash image"),
                        "author": img["user"]["name"] if "user" in img else "Unknown",
                        "likes": img.get("likes", 0)
                    })
                
                api_results['unsplash'] = {'success': True, 'count': len(results), 'error': None}
                print(f"✅ Unsplash: {len(results)} images")
            else:
                error_msg = f"Status {unsplash.status_code}: {unsplash.text}"
                api_results['unsplash']['error'] = error_msg
                print(f"❌ Unsplash error: {error_msg}")
                
        except Exception as e:
            api_results['unsplash']['error'] = str(e)
            print(f"❌ Unsplash exception: {e}")
    else:
        print("⚠️ Unsplash API key not configured")

    if PEXELS_API_KEY and PEXELS_API_KEY != "your_pexels_api_key_here": # Set your unsplash key env not set
        try:
            headers = {"Authorization": PEXELS_API_KEY}
            pexels_params = {
                "per_page": min(per_page // 4, 15),
                "page": page
            }
            
            if query:
                pexels_params["query"] = query
                pexels_url = "https://api.pexels.com/v1/search"
            else:
                pexels_url = "https://api.pexels.com/v1/curated"
                
            print(f"📡 Calling Pexels API: {pexels_url}")
            pexels = requests.get(pexels_url, headers=headers, params=pexels_params, timeout=10)
            
            print(f"Pexels response status: {pexels.status_code}")
            
            if pexels.ok:
                data = pexels.json()
                photos = data.get("photos", [])
                total_pages = max(total_pages, (data.get("total_results", 500) // per_page) + 1)
                
                for img in photos[:per_page//4]:
                    all_images.append({
                        "url": img["src"]["large"],
                        "thumbnail": img["src"]["medium"],
                        "source": "pexels",
                        "alt": img.get("alt", "Pexels image"),
                        "author": img.get("photographer", "Unknown"),
                        "likes": random.randint(50, 5000)
                    })
                
                api_results['pexels'] = {'success': True, 'count': len(photos), 'error': None}
            else:
                error_msg = f"Status {pexels.status_code}: {pexels.text}"
                api_results['pexels']['error'] = error_msg
                print(f"❌ Pexels error: {error_msg}")
                
        except Exception as e:
            api_results['pexels']['error'] = str(e)
            print(f"❌ Pexels exception: {e}")
    else:
        print("⚠️ Pexels API key not configured")

    if not query or any(word in query.lower() for word in ["anime", "cat", "neko", "cute", "pixel"]):
        try:
            print("📡 Calling Nekos API")
            for i in range(min(3, per_page // 8)):
                neko = requests.get("https://nekos.life/api/v2/img/neko", timeout=10)
                if neko.ok:
                    img_data = neko.json()
                    all_images.append({
                        "url": img_data["url"],
                        "thumbnail": img_data["url"],
                        "source": "nekos",
                        "alt": "Neko anime image",
                        "author": "Nekos.life",
                        "likes": random.randint(10, 1000)
                    })
                    
            api_results['nekos'] = {'success': True, 'count': min(3, per_page // 8), 'error': None}
            print(f"✅ Nekos: {min(3, per_page // 8)} images")
        except Exception as e:
            api_results['nekos']['error'] = str(e)
            print(f"❌ Nekos exception: {e}")

    try:
        chicago_params = {
            "limit": min(per_page // 6, 8),
            "page": page,
            "fields": "image_id,title,artist_title"
        }
        
        if query:
            chicago_params["q"] = query
            chicago_url = "https://api.artic.edu/api/v1/artworks/search"
        else:
            chicago_url = "https://api.artic.edu/api/v1/artworks"
            
        print(f"📡 Calling Art Institute API: {chicago_url}")
        chicago = requests.get(chicago_url, params=chicago_params, timeout=10)
        
        print(f"Art Institute response status: {chicago.status_code}")
        
        if chicago.ok:
            data = chicago.json()
            artworks = data.get("data", [])
            
            for art in artworks:
                img_id = art.get("image_id")
                if img_id:
                    all_images.append({
                        "url": f"https://www.artic.edu/iiif/2/{img_id}/full/843,/0/default.jpg",
                        "thumbnail": f"https://www.artic.edu/iiif/2/{img_id}/full/400,/0/default.jpg",
                        "source": "artic",
                        "alt": art.get("title", "Art Institute artwork"),
                        "author": art.get("artist_title", "Unknown Artist"),
                        "likes": random.randint(100, 10000)
                    })
            
            api_results['artic'] = {'success': True, 'count': len(artworks), 'error': None}
            print(f"✅ Art Institute: {len(artworks)} images")
        else:
            error_msg = f"Status {chicago.status_code}: {chicago.text}"
            api_results['artic']['error'] = error_msg
            print(f"❌ Art Institute error: {error_msg}")
            
    except Exception as e:
        api_results['artic']['error'] = str(e)
        print(f"❌ Art Institute exception: {e}")

    random.shuffle(all_images)
    all_images = all_images[:per_page]
    
    if query:
        total_pages = min(total_pages, 20)
    else:
        total_pages = 50

    print(f"\n📊 SUMMARY:")
    print(f"Total images collected: {len(all_images)}")
    for api, result in api_results.items():
        status = "✅" if result['success'] else "❌"
        error = f" - {result['error']}" if result['error'] else ""
        print(f"{status} {api.capitalize()}: {result['count']} images{error}")

    response_data = {
        "images": all_images,
        "current_page": page,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1,
        "debug": api_results
    }
    
    return jsonify(response_data)

@app.route('/wallpaper')
def wallpaper_page():
    return render_template('wallpaper.html')

@app.route('/wallpaper/random')
def get_random_wallpapers():
    random_query = random.choice(RANDOM_WALLPAPER_QUERIES)
    images = fetch_wallpaperflare_images(random_query, 1)
    return jsonify({
        'images': images, 
        'query': random_query, 
        'page': 1,
        'is_random': True
    })

@app.route('/wallpaper/search')
def search_wallpapers():
    query = request.args.get('query', '')
    page = int(request.args.get('page', 1))
    
    if not query:
        return jsonify({'images': [], 'error': 'No query provided'})
    
    images = fetch_wallpaperflare_images(query, page)
    return jsonify({
        'images': images, 
        'query': query, 
        'page': page,
        'is_random': False
    })

@app.route('/related_images')
def get_related_images():
    source = request.args.get('source', 'unsplash')
    query = request.args.get('query', '')
    page = int(request.args.get('page', 1))
    per_page = 100

    related_images = []

    if source == 'wallpaperflare':
        if not query:
            query = random.choice(RANDOM_WALLPAPER_QUERIES)
        related_images = fetch_wallpaperflare_images(query, page)
        related_images = [{
            "url": img_url,
            "thumbnail": img_url,
            "source": "wallpaperflare",
            "alt": query,
            "author": "WallpaperFlare",
            "likes": random.randint(100, 10000)
        } for img_url in related_images[:per_page]]

    else:
        temp_response = fetch_images_internal(query=query, page=page, per_page=per_page * 2)
        
        related_images = [img for img in temp_response['images'] if img['source'] == source][:per_page]

        if not related_images and query:
             temp_response = fetch_images_internal(query=query, page=page, per_page=per_page)
             related_images = temp_response['images'][:per_page]


    return jsonify({
        "images": related_images,
        "query": query,
        "source": source
    })

def fetch_images_internal(query="", page=1, per_page=20):
    all_images = []
    total_pages = 1
    
    if UNSPLASH_ACCESS_KEY and UNSPLASH_ACCESS_KEY != "your_unsplash_access_key_here":
        try:
            unsplash_params = {
                "page": page,
                "per_page": min(per_page // 2, 50),
                "client_id": UNSPLASH_ACCESS_KEY
            }
            if query:
                unsplash_params["query"] = query
                unsplash_url = "https://api.unsplash.com/search/photos"
            else:
                unsplash_url = "https://api.unsplash.com/photos"
            unsplash = requests.get(unsplash_url, params=unsplash_params, timeout=10)
            if unsplash.ok:
                data = unsplash.json()
                results = data.get("results", []) if query else data
                total_pages = max(total_pages, data.get("total_pages", 1) if query else 50)
                for img in results[:per_page//2]:
                    all_images.append({
                        "url": img["urls"]["regular"],
                        "thumbnail": img["urls"]["small"],
                        "source": "unsplash",
                        "alt": img.get("alt_description", "Unsplash image"),
                        "author": img["user"]["name"] if "user" in img else "Unknown",
                        "likes": img.get("likes", 0)
                    })
        except Exception as e:
            print(f"❌ Unsplash exception in internal fetch: {e}")

    if PEXELS_API_KEY and PEXELS_API_KEY != "your_pexels_api_key_here":
        try:
            headers = {"Authorization": PEXELS_API_KEY}
            pexels_params = {
                "per_page": min(per_page // 2, 50),
                "page": page
            }
            if query:
                pexels_params["query"] = query
                pexels_url = "https://api.pexels.com/v1/search"
            else:
                pexels_url = "https://api.pexels.com/v1/curated"
            pexels = requests.get(pexels_url, headers=headers, params=pexels_params, timeout=10)
            if pexels.ok:
                data = pexels.json()
                photos = data.get("photos", [])
                total_pages = max(total_pages, (data.get("total_results", 500) // per_page) + 1)
                for img in photos[:per_page//2]:
                    all_images.append({
                        "url": img["src"]["large"],
                        "thumbnail": img["src"]["medium"],
                        "source": "pexels",
                        "alt": img.get("alt", "Pexels image"),
                        "author": img.get("photographer", "Unknown"),
                        "likes": random.randint(50, 5000)
                    })
        except Exception as e:
            print(f"❌ Pexels exception in internal fetch: {e}")

    if not query or any(word in query.lower() for word in ["anime", "cat", "neko", "cute", "pixel"]):
        try:
            for i in range(min(per_page // 4, 25)):
                neko = requests.get("https://nekos.life/api/v2/img/neko", timeout=10)
                if neko.ok:
                    img_data = neko.json()
                    all_images.append({
                        "url": img_data["url"],
                        "thumbnail": img_data["url"],
                        "source": "nekos",
                        "alt": "Neko anime image",
                        "author": "Nekos.life",
                        "likes": random.randint(10, 1000)
                    })
        except Exception as e:
            print(f"❌ Nekos exception in internal fetch: {e}")

    try:
        chicago_params = {
            "limit": min(per_page // 4, 25),
            "page": page,
            "fields": "image_id,title,artist_title"
        }
        if query:
            chicago_params["q"] = query
            chicago_url = "https://api.artic.edu/api/v1/artworks/search"
        else:
            chicago_url = "https://api.artic.edu/api/v1/artworks"
        chicago = requests.get(chicago_url, params=chicago_params, timeout=10)
        if chicago.ok:
            data = chicago.json()
            artworks = data.get("data", [])
            for art in artworks:
                img_id = art.get("image_id")
                if img_id:
                    all_images.append({
                        "url": f"https://www.artic.edu/iiif/2/{img_id}/full/843,/0/default.jpg",
                        "thumbnail": f"https://www.artic.edu/iiif/2/{img_id}/full/400,/0/default.jpg",
                        "source": "artic",
                        "alt": art.get("title", "Art Institute artwork"),
                        "author": art.get("artist_title", "Unknown Artist"),
                        "likes": random.randint(100, 10000)
                    })
    except Exception as e:
        print(f"❌ Art Institute exception in internal fetch: {e}")

    random.shuffle(all_images)
    all_images = all_images[:per_page]
    
    if query:
        total_pages = min(total_pages, 20)
    else:
        total_pages = 50

    return {
        "images": all_images,
        "current_page": page,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1,
    }

@app.route("/test")
def test_apis():
    """Test endpoint to check API connectivity"""
    results = {}
    
    try:
        neko = requests.get("https://nekos.life/api/v2/img/neko", timeout=5)
        results['nekos'] = {
            'status': neko.status_code,
            'working': neko.ok,
            'response': neko.json() if neko.ok else neko.text
        }
    except Exception as e:
        results['nekos'] = {'status': 'error', 'working': False, 'error': str(e)}
    
    try:
        art = requests.get("https://api.artic.edu/api/v1/artworks?limit=1&fields=image_id,title", timeout=5)
        results['artic'] = {
            'status': art.status_code,
            'working': art.ok,
            'response': art.json() if art.ok else art.text
        }
    except Exception as e:
        results['artic'] = {'status': 'error', 'working': False, 'error': str(e)}
    
    return jsonify(results)

if __name__ == "__main__":
    print("🚀 Starting Flask app with debug logging...")
    print("📝 Visit http://localhost:5000/test to check API connectivity")
    app.run(debug=True)
