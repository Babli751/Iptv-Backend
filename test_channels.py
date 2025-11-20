#!/usr/bin/env python3
"""
IPTV Channel Testing Script
Tests all configured channels for availability and stream quality
"""

import requests
import time
from datetime import datetime
from colorama import init, Fore, Style
import sys

# Initialize colorama for colored output
init(autoreset=True)

# Channels to test (from channels.py)
CHANNELS = [
    {
        "name": "&pictures",
        "url": "http://51.254.122.232:5005/stream/tata/pictures/master.m3u8?u=atech&p=1491fed6b7de88547a8fd33cdb98e457a54e142527b1b59f6c0502a8a87fb6bb",
        "re_stream_id": "and_pictures",
    },
    {
        "name": "7x Music",
        "url": "http://51.254.122.232:5005/stream/tata/7xmusic/master.m3u8?u=atech&p=1491fed6b7de88547a8fd33cdb98e457a54e142527b1b59f6c0502a8a87fb6bb",
        "re_stream_id": "7x_music",
    },
    {
        "name": "&TV",
        "url": "http://51.254.122.232:5005/stream/tata/tv/master.m3u8?u=atech&p=1491fed6b7de88547a8fd33cdb98e457a54e142527b1b59f6c0502a8a87fb6bb",
        "re_stream_id": "and_tv",
    },
    {
        "name": "Animal Planet HD World",
        "url": "http://51.254.122.232:5005/stream/tata/animalplanethdworld/master.m3u8?u=atech&p=1491fed6b7de88547a8fd33cdb98e457a54e142527b1b59f6c0502a8a87fb6bb",
        "re_stream_id": "animal_planet",
    },
    {
        "name": "Jantantra TV",
        "url": "http://51.254.122.232:5005/stream/tata/jantantratv/master.m3u8?u=atech&p=1491fed6b7de88547a8fd33cdb98e457a54e142527b1b59f6c0502a8a87fb6bb",
        "re_stream_id": "jantantra_tv",
    },
    {
        "name": "Jaya Max",
        "url": "http://51.254.122.232:5005/stream/tata/jayamax/master.m3u8?u=atech&p=1491fed6b7de88547a8fd33cdb98e457a54e142527b1b59f6c0502a8a87fb6bb",
        "re_stream_id": "jaya_max",
    },
    {
        "name": "Bollywood Premiere",
        "url": "http://51.254.122.232:5005/stream/tata/tataplaybollywoodpremiere/master.m3u8?u=atech&p=1491fed6b7de88547a8fd33cdb98e457a54e142527b1b59f6c0502a8a87fb6bb",
        "re_stream_id": "bollywood_premiere",
    },
    {
        "name": "Al Jazeera",
        "url": "http://51.254.122.232:5005/stream/tata/aljazeera/master.m3u8?u=atech&p=1491fed6b7de88547a8fd33cdb98e457a54e142527b1b59f6c0502a8a87fb6bb",
        "re_stream_id": "al_jazeera",
    },
    {
        "name": "ANN News",
        "url": "http://51.254.122.232:5005/stream/tata/annnews/master.m3u8?u=atech&p=1491fed6b7de88547a8fd33cdb98e457a54e142527b1b59f6c0502a8a87fb6bb",
        "re_stream_id": "ann_news",
    }
]

def print_header():
    """Print test header"""
    print("\n" + "="*70)
    print(f"{Fore.CYAN}{Style.BRIGHT}IPTV CHANNEL TEST SUITE")
    print(f"{Fore.YELLOW}Test Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70 + "\n")

def print_footer(results):
    """Print test summary"""
    total = len(results)
    success = sum(1 for r in results if r['status'] == 'success')
    failed = total - success

    print("\n" + "="*70)
    print(f"{Fore.CYAN}{Style.BRIGHT}TEST SUMMARY")
    print("="*70)
    print(f"Total Channels: {total}")
    print(f"{Fore.GREEN}✓ Successful: {success}")
    print(f"{Fore.RED}✗ Failed: {failed}")
    print(f"Success Rate: {(success/total*100):.1f}%")
    print("="*70 + "\n")

def test_channel(channel, timeout=10):
    """
    Test a single channel stream

    Args:
        channel: Channel dictionary with name, url, and re_stream_id
        timeout: Request timeout in seconds

    Returns:
        Dictionary with test results
    """
    result = {
        'name': channel['name'],
        'id': channel['re_stream_id'],
        'url': channel['url'],
        'status': 'unknown',
        'status_code': None,
        'response_time': None,
        'content_type': None,
        'content_length': None,
        'error': None
    }

    print(f"{Fore.CYAN}Testing: {Style.BRIGHT}{channel['name']}{Style.RESET_ALL} ({channel['re_stream_id']})")

    try:
        start_time = time.time()
        response = requests.get(
            channel['url'],
            timeout=timeout,
            stream=True,
            headers={'User-Agent': 'VLC/3.0.0'}
        )
        response_time = time.time() - start_time

        result['status_code'] = response.status_code
        result['response_time'] = round(response_time, 2)
        result['content_type'] = response.headers.get('Content-Type', 'Unknown')
        result['content_length'] = response.headers.get('Content-Length', 'Unknown')

        if response.status_code == 200:
            # Try to read first chunk to verify stream is working
            try:
                chunk = next(response.iter_content(chunk_size=8192))
                if chunk:
                    result['status'] = 'success'
                    print(f"  {Fore.GREEN}✓ SUCCESS - Status: {response.status_code}, Time: {result['response_time']}s")
                    print(f"    Content-Type: {result['content_type']}")
                else:
                    result['status'] = 'failed'
                    result['error'] = 'Empty stream'
                    print(f"  {Fore.RED}✗ FAILED - Empty stream")
            except Exception as e:
                result['status'] = 'failed'
                result['error'] = f'Stream read error: {str(e)}'
                print(f"  {Fore.RED}✗ FAILED - {result['error']}")
        else:
            result['status'] = 'failed'
            result['error'] = f'HTTP {response.status_code}'
            print(f"  {Fore.RED}✗ FAILED - HTTP Status: {response.status_code}")

    except requests.exceptions.Timeout:
        result['status'] = 'failed'
        result['error'] = f'Timeout after {timeout}s'
        print(f"  {Fore.RED}✗ FAILED - Timeout after {timeout}s")

    except requests.exceptions.ConnectionError as e:
        result['status'] = 'failed'
        result['error'] = 'Connection error'
        print(f"  {Fore.RED}✗ FAILED - Connection error")

    except Exception as e:
        result['status'] = 'failed'
        result['error'] = str(e)
        print(f"  {Fore.RED}✗ FAILED - {str(e)}")

    print()  # Empty line for readability
    return result

def test_api_endpoint(base_url="http://localhost:8000"):
    """Test if the API server is running"""
    print(f"{Fore.CYAN}Checking API server at {base_url}...")
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            print(f"{Fore.GREEN}✓ API server is running\n")
            return True
        else:
            print(f"{Fore.YELLOW}⚠ API server returned status {response.status_code}\n")
            return False
    except Exception as e:
        print(f"{Fore.RED}✗ API server is not accessible: {str(e)}\n")
        return False

def main():
    """Main test function"""
    print_header()

    # Test API server (optional)
    api_running = test_api_endpoint()
    if api_running:
        print(f"{Fore.GREEN}You can also test through API at:")
        print(f"  http://localhost:8000/api/v1/channels/static-original-m3u")
        print(f"  http://localhost:8000/api/v1/channels/test-vlc-debug\n")
        print("="*70 + "\n")

    # Test all channels
    results = []
    for i, channel in enumerate(CHANNELS, 1):
        print(f"{Fore.MAGENTA}[{i}/{len(CHANNELS)}]", end=" ")
        result = test_channel(channel)
        results.append(result)

        # Small delay between tests to avoid overwhelming the server
        if i < len(CHANNELS):
            time.sleep(0.5)

    # Print summary
    print_footer(results)

    # Print failed channels details
    failed_channels = [r for r in results if r['status'] == 'failed']
    if failed_channels:
        print(f"{Fore.RED}{Style.BRIGHT}FAILED CHANNELS DETAILS:")
        print("-"*70)
        for r in failed_channels:
            print(f"{Fore.RED}Channel: {r['name']}")
            print(f"  ID: {r['id']}")
            print(f"  Error: {r['error']}")
            print(f"  URL: {r['url'][:80]}...")
            print()

    # Return exit code based on results
    return 0 if len(failed_channels) == 0 else 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}Test interrupted by user")
        sys.exit(130)
