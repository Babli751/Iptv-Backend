# HLS Streaming with 10-Second Buffer

This implementation provides optimized HLS (HTTP Live Streaming) functionality that maintains only the last 10 seconds of stream data for reduced buffering and better performance.

## Features

- **Low Latency**: 2-second segments with only 5 segments kept (10 seconds total)
- **Automatic Cleanup**: Old segments are automatically removed to save disk space
- **Reconnection**: Auto-reconnect on stream failures
- **Health Monitoring**: Real-time status of all streams

## API Endpoints

### Start a Stream
```
GET /api/v1/channels/start-stream/{channel_name}
```
Starts HLS streaming for a specific channel.

**Example:**
```bash
curl http://localhost:8000/api/v1/channels/start-stream/and_pictures
```

**Response:**
```json
{
  "message": "FFmpeg process for 'and_pictures' started.",
  "channel": "&pictures",
  "hls_url": "/hls_streams/and_pictures/master.m3u8",
  "config": {
    "segment_duration": 2,
    "max_segments": 5,
    "cleanup_interval": 5
  }
}
```

### Stop a Stream
```
GET /api/v1/channels/stop-stream/{channel_name}
```

### Check Stream Status
```
GET /api/v1/channels/stream-status/{channel_name}
```

**Response:**
```json
{
  "channel_name": "&pictures",
  "stream_id": "and_pictures",
  "process_status": "running",
  "cleanup_running": true,
  "segment_count": 5,
  "max_segments": 5,
  "master_playlist_exists": true,
  "hls_url": "/hls_streams/and_pictures/master.m3u8",
  "estimated_buffer_seconds": 10
}
```

### Check All Streams Status
```
GET /api/v1/channels/streams-status
```

### Get HLS Playlist
```
GET /api/v1/channels/static-hls-m3u
```
Returns an M3U playlist with HLS URLs for all channels.

## How It Works

1. **Stream Processing**: FFmpeg processes the original M3U8 stream and creates 2-second segments
2. **Buffer Management**: Only keeps the last 5 segments (10 seconds total)
3. **Automatic Cleanup**: Background thread removes old segments every 5 seconds
4. **Serving**: FastAPI serves the HLS files as static content

## Configuration

The HLS behavior can be modified by updating `HLS_CONFIG` in `channels.py`:

```python
HLS_CONFIG = {
    "segment_duration": 2,  # Seconds per segment
    "max_segments": 5,      # Number of segments to keep
    "cleanup_interval": 5,  # Cleanup frequency in seconds
}
```

## Usage Flow

1. Start the FastAPI server
2. Call `/start-stream/{channel_name}` to begin streaming
3. Access the HLS stream at `/hls_streams/{channel_name}/master.m3u8`
4. Monitor status with `/stream-status/{channel_name}`
5. Stop with `/stop-stream/{channel_name}` when done

## Benefits

- **Reduced Buffering**: Only 10 seconds of content buffered
- **Lower Storage**: Automatic cleanup prevents disk space issues  
- **Better Performance**: Copy codecs avoid re-encoding overhead
- **Reliability**: Auto-reconnection handles stream interruptions
- **Monitoring**: Real-time status tracking for all streams

## Requirements

- FFmpeg installed and available in system PATH
- FastAPI application running
- Network access to original M3U8 streams

## File Structure

```
hls_streams/
├── and_pictures/
│   ├── master.m3u8
│   ├── segment_20231201_143022_000.ts
│   ├── segment_20231201_143024_001.ts
│   └── ... (max 5 segments)
├── 7x_music/
│   └── ...
└── ...
```
