import asyncio
import aiohttp
from pytube import YouTube
import moviepy.editor as mp

async def fetch_data(url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.read()

    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

async def get_video_info(video_url):
    try:
        yt = YouTube(video_url)
        title = yt.title
        thumbnail_url = yt.thumbnail_url

        # Download the thumbnail image
        thumbnail_data = await fetch_data(thumbnail_url)

        return title, thumbnail_data, yt.streams

    except Exception as e:
        print(f"Error: {e}")
        return None, None, None

async def download_and_combine(video_url, output_path, video_format, audio_format):
    try:
        yt = YouTube(video_url)
        video_stream = yt.streams.get_by_itag(video_format)
        audio_stream = yt.streams.get_by_itag(audio_format)

        print(f"Downloading: {yt.title}...")

        # Download video and audio separately
        video_path = rf"{output_path}\video{yt.title}.{video_stream.subtype}"
        audio_path = rf"{output_path}audio{yt.title}.{audio_stream.subtype}"  # Use audio stream subtype as extension
        video_stream.download(output_path, filename_prefix="video")
        audio_stream.download(output_path, filename_prefix="audio")

        # Combine video and audio using MoviePy
        clip = mp.VideoFileClip(video_path)
        audio = mp.AudioFileClip(audio_path)
        video_with_audio = clip.set_audio(audio)
        final_path = f"{output_path}{yt.title}_final.mp4"
        video_with_audio.write_videofile(final_path)

        print(f"Download and combination completed! Saved as: {final_path}")

    except Exception as e:
        print(f"Error: {e}")

async def main():
    video_url = "https://youtu.be/AP55-ysy6xo?si=l2ZJCUYd5Ewzkm1S"
    output_path = r"D:\CodeBase\Downloader"

    title, thumbnail_data, streams = await get_video_info(video_url)

    if title and thumbnail_data and streams:
        print(f"Title: {title}")

        # Display available formats
        print("Available Formats:")
        for i, stream in enumerate(streams):
            print(f"{i + 1}. {stream}")

        # Input selection
        try:
            video_format_index = int(input("Enter the number for the video format: ")) - 1
            audio_format_index = int(input("Enter the number for the audio format: ")) - 1

            video_format = streams[video_format_index].itag
            audio_format = streams[audio_format_index].itag

            # Save thumbnail image
            thumbnail_path = f"{output_path}{title}_thumbnail.jpg"
            with open(thumbnail_path, 'wb') as file:
                file.write(thumbnail_data)

            # Download and combine video and audio
            await download_and_combine(video_url, output_path, video_format, audio_format)

        except (ValueError, IndexError):
            print("Invalid input. Please enter valid numbers.")

if __name__ == "__main__":
    asyncio.run(main())
