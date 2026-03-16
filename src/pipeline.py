import select_frame
import insert_product
import flux


def run_pipeline(video_path, product_path, product_description):
    result = select_frame.find_best_product_placement_shot(
    video_path=video_path
    )
    
    result = json.dumps(result, indent=2)
    
    begin_frame = results["best_shot_start_frame"] # 78
    end_frame = results["best_shot_end_frame"] # 170
    
    
    video = cv2.VideoCapture(video_path)
    if not video.isOpened():
        print(f"Error: Could not open video file. Make sure '{video_path}' exists.")
        exit()
    video.set(cv2.CAP_PROP_POS_FRAMES, begin_frame)
    success, frame = video.read()
    if success:
        cv2.imwrite("first_frame.png", frame)
        print(f"Frame {begin_frame} saved as first_frame.png")
    else:
        print(f"Failed to read frame {begin_frame}")
    video.release()
    
    
    background = "first_frame.png"
    product = product_path
    
    final_image, bbox_coords = recursive_placement(background, product, product_description)
    
    flux_output, filename = flux.place_product(background, product, bbox_coords, product_description)
    
    generate_video(filename, video_path, begin_frame, end_frame, bbox_coords)