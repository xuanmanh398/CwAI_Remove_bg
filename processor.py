import os
import cv2
import time
import numpy as np
from PIL import Image, ImageFilter
from rembg import remove, new_session
import moviepy as mp

class VideoBGRemover:
    def __init__(self):
        self.sessions = {}

    def get_rembg_session(self, model_name="u2net"):
        """Cached rembg session creation."""
        if model_name not in self.sessions:
            self.sessions[model_name] = new_session(model_name)
        return self.sessions[model_name]

    def process_frame_rembg(self, frame_bgr, model_name="u2net", alpha_matting=False):
        """
        Process a single BGR frame using rembg AI.
        Returns:
            fg_rgba: RGBA numpy array (H, W, 4)
            mask: Gray scale numpy array mask (H, W), values 0..255
        """
        # Convert BGR (OpenCV) to RGB (PIL)
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(frame_rgb)
        
        session = self.get_rembg_session(model_name)
        res_pil = remove(
            pil_img, 
            session=session, 
            alpha_matting=alpha_matting,
            alpha_matting_foreground_threshold=240,
            alpha_matting_background_threshold=10,
            alpha_matting_erode_size=10
        )
        
        res_rgba = np.array(res_pil)
        mask = res_rgba[:, :, 3]
        return res_rgba, mask

    def apply_background(
        self, 
        frame_bgr, 
        mask, 
        bg_type="color", 
        bg_color=(0, 255, 0), 
        bg_image_rgb=None, 
        bg_frame_bgr=None, 
        blur_radius=15, 
        feather_amount=3
    ):
        """
        Composites foreground frame onto desired background type.
        
        bg_type:
            - "transparent": Chroma Key Green/Black or RGBA output
            - "color": BGR color tuple (B, G, R)
            - "image": RGB numpy array for background image
            - "video": BGR numpy array for background video frame
            - "blur": Blurred version of original frame_bgr
        """
        h, w, c = frame_bgr.shape
        
        # Smooth mask edge if requested
        if feather_amount > 0:
            ksize = feather_amount * 2 + 1
            mask_smooth = cv2.GaussianBlur(mask, (ksize, ksize), 0)
        else:
            mask_smooth = mask

        alpha = (mask_smooth.astype(float) / 255.0)[:, :, np.newaxis]

        if bg_type == "color":
            bg = np.zeros_like(frame_bgr, dtype=np.uint8)
            bg[:] = bg_color  # BGR
        elif bg_type == "image" and bg_image_rgb is not None:
            # Resize image to match video dimensions
            bg_resized = cv2.resize(bg_image_rgb, (w, h))
            bg = cv2.cvtColor(bg_resized, cv2.COLOR_RGB2BGR)
        elif bg_type == "video" and bg_frame_bgr is not None:
            bg = cv2.resize(bg_frame_bgr, (w, h))
        elif bg_type == "blur":
            ksize = blur_radius if blur_radius % 2 == 1 else blur_radius + 1
            bg = cv2.GaussianBlur(frame_bgr, (ksize, ksize), 0)
        elif bg_type == "transparent":
            # Return RGBA frame directly
            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            rgba = np.dstack((frame_rgb, mask_smooth))
            return rgba
        else:
            # Default Green Screen (0, 255, 0)
            bg = np.zeros_like(frame_bgr, dtype=np.uint8)
            bg[:] = (0, 255, 0)

        # Alpha blend: output = alpha * fg + (1 - alpha) * bg
        composite = (alpha * frame_bgr + (1.0 - alpha) * bg).astype(np.uint8)
        return composite

    def get_video_info(self, video_path):
        """Extract video metadata: fps, total_frames, width, height, duration."""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Không thể mở file video: {video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = total_frames / fps if fps > 0 else 0
        cap.release()
        
        return {
            "fps": fps if fps > 0 else 30.0,
            "total_frames": total_frames,
            "width": width,
            "height": height,
            "duration": duration
        }

    def get_preview_frame(
        self, 
        video_path, 
        frame_time_sec=0.0, 
        model_name="u2net", 
        bg_type="color", 
        bg_color=(0, 255, 0), 
        bg_image_rgb=None, 
        blur_radius=15, 
        feather_amount=3
    ):
        """Returns original RGB frame and processed RGB frame for UI preview."""
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        target_frame = int(frame_time_sec * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
        
        ret, frame_bgr = cap.read()
        cap.release()
        
        if not ret or frame_bgr is None:
            raise ValueError(f"Không thể đọc frame tại giây {frame_time_sec}")

        original_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        
        _, mask = self.process_frame_rembg(frame_bgr, model_name=model_name)
        
        comp = self.apply_background(
            frame_bgr=frame_bgr,
            mask=mask,
            bg_type=bg_type,
            bg_color=bg_color,
            bg_image_rgb=bg_image_rgb,
            blur_radius=blur_radius,
            feather_amount=feather_amount
        )
        
        if bg_type == "transparent":
            processed_pil = Image.fromarray(comp, mode="RGBA")
        else:
            processed_rgb = cv2.cvtColor(comp, cv2.COLOR_BGR2RGB)
            processed_pil = Image.fromarray(processed_rgb, mode="RGB")
            
        return Image.fromarray(original_rgb), processed_pil

    def process_video(
        self, 
        video_path, 
        output_path, 
        model_name="u2net", 
        bg_type="color", 
        bg_color=(0, 255, 0), 
        bg_image_rgb=None, 
        bg_video_path=None,
        blur_radius=15, 
        feather_amount=3,
        scale=1.0,
        progress_callback=None
    ):
        """
        Process the entire video frame by frame, preserving original audio.
        """
        info = self.get_video_info(video_path)
        cap_main = cv2.VideoCapture(video_path)
        
        cap_bg = None
        if bg_type == "video" and bg_video_path and os.path.exists(bg_video_path):
            cap_bg = cv2.VideoCapture(bg_video_path)

        out_w = int(info["width"] * scale)
        out_h = int(info["height"] * scale)
        fps = info["fps"]
        total_frames = info["total_frames"]

        # Temporary video output file for video stream
        temp_video_out = output_path + ".temp.mp4"
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        
        if bg_type == "transparent":
            # Write as mp4 with green background for standard player compatibility or MOV
            # Most web browsers cannot play raw transparent MP4, so we write green or black keying
            # But let's create high quality mp4
            writer = cv2.VideoWriter(temp_video_out, fourcc, fps, (out_w, out_h))
        else:
            writer = cv2.VideoWriter(temp_video_out, fourcc, fps, (out_w, out_h))

        start_time = time.time()
        frame_idx = 0

        while True:
            ret, frame_bgr = cap_main.read()
            if not ret or frame_bgr is None:
                break

            if scale != 1.0:
                frame_bgr = cv2.resize(frame_bgr, (out_w, out_h))

            bg_frame_bgr = None
            if cap_bg:
                ret_bg, bg_frame_bgr = cap_bg.read()
                if not ret_bg or bg_frame_bgr is None:
                    # Loop background video if shorter
                    cap_bg.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret_bg, bg_frame_bgr = cap_bg.read()

            _, mask = self.process_frame_rembg(frame_bgr, model_name=model_name)

            comp = self.apply_background(
                frame_bgr=frame_bgr,
                mask=mask,
                bg_type="color" if bg_type == "transparent" else bg_type,
                bg_color=bg_color if bg_type != "transparent" else (0, 255, 0), # Chroma key green for transparent choice
                bg_image_rgb=bg_image_rgb,
                bg_frame_bgr=bg_frame_bgr,
                blur_radius=blur_radius,
                feather_amount=feather_amount
            )

            writer.write(comp)
            frame_idx += 1

            if progress_callback:
                elapsed = time.time() - start_time
                current_fps = frame_idx / elapsed if elapsed > 0 else 0
                eta = (total_frames - frame_idx) / current_fps if current_fps > 0 else 0
                progress_callback(frame_idx, total_frames, current_fps, eta)

        cap_main.release()
        if cap_bg:
            cap_bg.release()
        writer.release()

        # Combine audio from input video into temp output video using moviepy
        self.merge_audio(video_path, temp_video_out, output_path)

        if os.path.exists(temp_video_out):
            try:
                os.remove(temp_video_out)
            except Exception:
                pass

        return output_path

    def merge_audio(self, src_video_path, temp_video_path, final_output_path):
        """Combine original video audio track into newly processed video file."""
        try:
            video_clip = mp.VideoFileClip(temp_video_path)
            src_clip = mp.VideoFileClip(src_video_path)
            
            if src_clip.audio is not None:
                final_clip = video_clip.with_audio(src_clip.audio)
                final_clip.write_videofile(
                    final_output_path, 
                    codec="libx264", 
                    audio_codec="aac", 
                    logger=None
                )
                video_clip.close()
                src_clip.close()
                final_clip.close()
            else:
                # No audio track, just rename temp video
                video_clip.close()
                src_clip.close()
                if os.path.exists(final_output_path):
                    os.remove(final_output_path)
                os.rename(temp_video_path, final_output_path)
        except Exception as e:
            print(f"Audio merge notice: {e}, saving video without audio.")
            if os.path.exists(final_output_path):
                os.remove(final_output_path)
            os.rename(temp_video_path, final_output_path)
