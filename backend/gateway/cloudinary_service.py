# """
# Cloudinary Service - Gateway Pattern for Image Upload
# Handles all Cloudinary integration for ShareBite application
# """

# import cloudinary
# import cloudinary.uploader
# from typing import Dict, Optional, BinaryIO
# from fastapi import HTTPException, UploadFile
# import os
# from datetime import datetime

# # Cloudinary Configuration
# cloudinary.config(
#     cloud_name="dledk0cg7",
#     api_key="369151841227135",
#     api_secret="xX71cDtIIvemLNu3WVi4LzZZZZM"
# )

# class CloudinaryGateway:
#     """
#     Gateway class for Cloudinary operations following the Gateway Architecture pattern
#     This class encapsulates all Cloudinary-related functionality
#     """
    
#     def __init__(self):
#         self.allowed_formats = ["jpg", "jpeg", "png", "gif", "bmp", "webp"]
#         self.max_file_size = 10 * 1024 * 1024  # 10MB
#         self.recipe_folder = "sharebite/recipes"
        
#     def validate_image(self, file: UploadFile) -> None:
#         """
#         Validate uploaded image file
        
#         Args:
#             file (UploadFile): The uploaded file to validate
            
#         Raises:
#             HTTPException: If validation fails
#         """
#         # Validate file type
#         allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/gif", "image/bmp", "image/webp"]
#         if file.content_type not in allowed_types:
#             raise HTTPException(
#                 status_code=400, 
#                 detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}"
#             )
        
#         # Note: File size validation will be done after reading the file content
        
#     async def upload_recipe_image(
#         self, 
#         file: UploadFile, 
#         user_id: int, 
#         recipe_id: Optional[int] = None
#     ) -> Dict[str, str]:
#         """
#         Upload recipe image to Cloudinary
        
#         Args:
#             file (UploadFile): The image file to upload
#             user_id (int): ID of the user uploading the image
#             recipe_id (Optional[int]): Recipe ID if available, None for pre-upload
            
#         Returns:
#             Dict[str, str]: Dictionary containing image URLs and metadata
            
#         Raises:
#             HTTPException: If upload fails
#         """
#         try:
#             # Validate the image
#             self.validate_image(file)
            
#             # Read file content for size validation
#             file_content = await file.read()
#             file_size = len(file_content)
            
#             # Validate file size
#             if file_size > self.max_file_size:
#                 raise HTTPException(
#                     status_code=400, 
#                     detail="File too large. Maximum size is 10MB"
#                 )
            
#             # Reset file pointer for upload
#             await file.seek(0)
            
#             # Generate unique public_id
#             timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#             if recipe_id:
#                 public_id = f"{self.recipe_folder}/recipe_{recipe_id}_{user_id}_{timestamp}"
#             else:
#                 public_id = f"{self.recipe_folder}/temp_{user_id}_{timestamp}"
            
#             # Upload to Cloudinary
#             upload_result = cloudinary.uploader.upload(
#                 file.file,
#                 public_id=public_id,
#                 folder=self.recipe_folder,
#                 resource_type="image",
#                 format="auto",  # Auto-optimize format
#                 quality="auto:good",  # Auto-optimize quality
#                 fetch_format="auto",  # Auto-deliver best format based on browser
#                 transformation=[
#                     {"width": 1200, "height": 800, "crop": "limit"},  # Limit max size
#                     {"quality": "auto:good"},  # Optimize quality
#                     {"fetch_format": "auto"}  # Auto format
#                 ],
#                 tags=[f"user_{user_id}", "recipe_image", "sharebitee"]
#             )
            
#             # Extract important information
#             result = {
#                 "url": upload_result["secure_url"],
#                 "public_id": upload_result["public_id"],
#                 "width": upload_result.get("width", 0),
#                 "height": upload_result.get("height", 0),
#                 "format": upload_result.get("format", ""),
#                 "bytes": upload_result.get("bytes", file_size),
#                 "created_at": upload_result.get("created_at", ""),
#                 # Generate different size URLs for responsive design
#                 "thumbnail_url": cloudinary.CloudinaryImage(upload_result["public_id"]).build_url(
#                     width=300, height=200, crop="fill", quality="auto:good"
#                 ),
#                 "medium_url": cloudinary.CloudinaryImage(upload_result["public_id"]).build_url(
#                     width=600, height=400, crop="fill", quality="auto:good"
#                 ),
#                 "large_url": cloudinary.CloudinaryImage(upload_result["public_id"]).build_url(
#                     width=1200, height=800, crop="limit", quality="auto:good"
#                 )
#             }
            
#             print(f"Image uploaded successfully to Cloudinary: {result['public_id']}")
#             return result
            
#         except HTTPException:
#             raise
#         except Exception as e:
#             print(f"Cloudinary upload error: {e}")
#             raise HTTPException(
#                 status_code=500, 
#                 detail=f"Failed to upload image to Cloudinary: {str(e)}"
#             )
    
#     def delete_image(self, public_id: str) -> bool:
#         """
#         Delete image from Cloudinary
        
#         Args:
#             public_id (str): The public ID of the image to delete
            
#         Returns:
#             bool: True if deletion was successful, False otherwise
#         """
#         try:
#             result = cloudinary.uploader.destroy(public_id)
#             return result.get("result") == "ok"
#         except Exception as e:
#             print(f"Failed to delete image from Cloudinary: {e}")
#             return False
    
#     def get_image_info(self, public_id: str) -> Optional[Dict]:
#         """
#         Get image information from Cloudinary
        
#         Args:
#             public_id (str): The public ID of the image
            
#         Returns:
#             Optional[Dict]: Image information if found, None otherwise
#         """
#         try:
#             result = cloudinary.api.resource(public_id)
#             return result
#         except Exception as e:
#             print(f"Failed to get image info from Cloudinary: {e}")
#             return None
    
#     def generate_transformation_url(
#         self, 
#         public_id: str, 
#         width: Optional[int] = None,
#         height: Optional[int] = None,
#         crop: str = "fill",
#         quality: str = "auto:good"
#     ) -> str:
#         """
#         Generate transformed image URL
        
#         Args:
#             public_id (str): The public ID of the image
#             width (Optional[int]): Target width
#             height (Optional[int]): Target height
#             crop (str): Crop mode
#             quality (str): Quality setting
            
#         Returns:
#             str: Transformed image URL
#         """
#         try:
#             transformations = {"quality": quality}
#             if width:
#                 transformations["width"] = width
#             if height:
#                 transformations["height"] = height
#             if width or height:
#                 transformations["crop"] = crop
                
#             return cloudinary.CloudinaryImage(public_id).build_url(**transformations)
#         except Exception as e:
#             print(f"Failed to generate transformation URL: {e}")
#             return ""


# # Singleton instance for use throughout the application
# cloudinary_gateway = CloudinaryGateway()