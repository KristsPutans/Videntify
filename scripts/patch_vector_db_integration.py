#!/usr/bin/env python3
"""
Patch Vector Database Integration

This script applies necessary changes to the identification API
endpoints to integrate them with the vector database functionality.
"""

import os
import re
import sys
from pathlib import Path

# Add the project root to the path so we can import modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def add_vector_db_to_video_identification(file_path):
    """Add vector database integration to the video identification endpoint."""
    with open(file_path, 'r') as file:
        content = file.read()
        
    # Find the feature extraction section in identify_video function
    pattern = r'(# Extract features from the video\s+features = feature_pipeline\.extract_features_from_video\(temp_path\)\s+)'
    pattern += r'(# Convert extracted features to format needed by matching engine\s+matching_features = \{\}\s+)'
    
    # Add vector database integration code
    replacement = r'\1# Store features in vector database if required\n'
    replacement += r'        vector_features_stored = False\n'
    replacement += r'        if params.save_query and current_user:\n'
    replacement += r'            # Iterate through features and store in vector database\n'
    replacement += r'            for feature_name, feature_vector in features.items():\n'
    replacement += r'                feat_type = None\n'
    replacement += r'                if "visual_cnn" in feature_name:\n'
    replacement += r'                    feat_type = FeatureType.CNN_FEATURES\n'
    replacement += r'                elif "visual_phash" in feature_name:\n'
    replacement += r'                    feat_type = FeatureType.PERCEPTUAL_HASH\n'
    replacement += r'                elif "visual_motion" in feature_name:\n'
    replacement += r'                    feat_type = FeatureType.MOTION_PATTERN\n'
    replacement += r'                elif "audio_fingerprint" in feature_name:\n'
    replacement += r'                    feat_type = FeatureType.AUDIO_SPECTROGRAM\n'
    replacement += r'                \n'
    replacement += r'                if feat_type:\n'
    replacement += r'                    try:\n'
    replacement += r'                        # Store feature vector in the vector database\n'
    replacement += r'                        feature_id = vector_db.store_video_feature(\n'
    replacement += r'                            video_id=query_id,\n'
    replacement += r'                            feature_type=feat_type,\n'
    replacement += r'                            feature_vector=feature_vector.vector,\n'
    replacement += r'                            metadata={"is_query": True, "query_type": "video"}\n'
    replacement += r'                        )\n'
    replacement += r'                        if feature_id:\n'
    replacement += r'                            vector_features_stored = True\n'
    replacement += r'                            logger.debug(f"Stored {feature_name} in vector database with ID {feature_id}")\n'
    replacement += r'                    except Exception as e:\n'
    replacement += r'                        logger.error(f"Error storing {feature_name} in vector database: {e}")\n'
    replacement += r'        \n'
    replacement += r'\2'
    
    modified_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    # Find the frame identification feature extraction section
    frame_pattern = r'(# Extract features from the frame\s+features = feature_pipeline\.extract_features_from_image\(temp_path\)\s+)'
    frame_pattern += r'(# Convert extracted features to format needed by matching engine\s+matching_features = \{\}\s+)'
    
    # Add vector database integration code for frame identification
    frame_replacement = r'\1# Store features in vector database if required\n'
    frame_replacement += r'        vector_features_stored = False\n'
    frame_replacement += r'        if params.save_query and current_user:\n'
    frame_replacement += r'            # Iterate through features and store in vector database\n'
    frame_replacement += r'            for feature_name, feature_vector in features.items():\n'
    frame_replacement += r'                feat_type = None\n'
    frame_replacement += r'                if "visual_cnn" in feature_name:\n'
    frame_replacement += r'                    feat_type = FeatureType.CNN_FEATURES\n'
    frame_replacement += r'                elif "visual_phash" in feature_name:\n'
    frame_replacement += r'                    feat_type = FeatureType.PERCEPTUAL_HASH\n'
    frame_replacement += r'                \n'
    frame_replacement += r'                if feat_type:\n'
    frame_replacement += r'                    try:\n'
    frame_replacement += r'                        # Store feature vector in the vector database\n'
    frame_replacement += r'                        feature_id = vector_db.store_video_feature(\n'
    frame_replacement += r'                            video_id=query_id,\n'
    frame_replacement += r'                            feature_type=feat_type,\n'
    frame_replacement += r'                            feature_vector=feature_vector.vector,\n'
    frame_replacement += r'                            metadata={"is_query": True, "query_type": "frame"}\n'
    replacement += r'                        )\n'
    frame_replacement += r'                        if feature_id:\n'
    frame_replacement += r'                            vector_features_stored = True\n'
    frame_replacement += r'                            logger.debug(f"Stored {feature_name} in vector database with ID {feature_id}")\n'
    frame_replacement += r'                    except Exception as e:\n'
    frame_replacement += r'                        logger.error(f"Error storing {feature_name} in vector database: {e}")\n'
    frame_replacement += r'        \n'
    frame_replacement += r'\2'
    
    modified_content = re.sub(frame_pattern, frame_replacement, modified_content, flags=re.DOTALL)
    
    # Write the modified content back to the file
    with open(file_path, 'w') as file:
        file.write(modified_content)
    
    print(f"Successfully integrated vector database with identification endpoints in {file_path}")

def main():
    """Main function to apply vector database integration patches."""
    identification_file = os.path.join(str(project_root), 'src', 'api', 'identification.py')
    
    if os.path.exists(identification_file):
        add_vector_db_to_video_identification(identification_file)
    else:
        print(f"Error: Could not find identification.py at {identification_file}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
