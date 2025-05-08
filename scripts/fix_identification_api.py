#!/usr/bin/env python3
"""
Fix Identification API script

This script fixes issues with vector database integration in the identification API.
"""

import os
import sys
import re
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

IDENTIFICATION_API_PATH = project_root / "src" / "api" / "identification.py"


def fix_direct_vector_db_calls():
    """Replace direct vector database calls with helper function."""
    # Read the identification.py file
    with open(IDENTIFICATION_API_PATH, 'r') as f:
        content = f.read()
    
    # Pattern to match direct vector database feature storage code blocks
    pattern = r"""# Store features in vector database if required\s+
        vector_features_stored = False\s+
        if params\.save_query and current_user:\s+
            # Iterate through features and store in vector database\s+
            for feature_name, feature_vector in features\.items\(\):\s+
                feat_type = None\s+
                if "visual_cnn" in feature_name:\s+
                    feat_type = FeatureType\.CNN_FEATURES\s+
                elif "visual_phash" in feature_name:\s+
                    feat_type = FeatureType\.PERCEPTUAL_HASH\s+
                elif "visual_motion" in feature_name:\s+
                    feat_type = FeatureType\.MOTION_PATTERN\s+
                elif "audio_fingerprint" in feature_name:\s+
                    feat_type = FeatureType\.AUDIO_SPECTROGRAM\s+
                \s+
                if feat_type:\s+
                    try:\s+
                        # Store feature vector in the vector database\s+
                        feature_id = vector_db\.store_video_feature\(\s+
                            video_id=query_id,\s+
                            feature_type=feat_type,\s+
                            feature_vector=feature_vector\.vector,\s+
                            metadata=\{"is_query": True, "query_type": "\w+"\}\s+
                        \)\s+
                        if feature_id:\s+
                            vector_features_stored = True\s+
                            logger\.debug\(f"Stored \{feature_name\} in vector database with ID \{feature_id\}"\)\s+
                    except Exception as e:\s+
                        logger\.error\(f"Error storing \{feature_name\} in vector database: \{e\}"\)"""
    
    # Replace with helper function
    replacement = """# Store features in vector database if required
        vector_features_stored = False
        if params.save_query and current_user:
            # Use the helper function to store features in vector database
            vector_features_stored = store_video_features_in_vector_db(
                vector_db=vector_db,
                query_id=query_id,
                features=features,
                save_query=params.save_query,
                query_type="$QUERY_TYPE"
            )"""
    
    # Find and replace all direct vector database call patterns
    for match in re.finditer(pattern, content):
        match_text = match.group(0)
        query_type_match = re.search(r'metadata=\{"is_query": True, "query_type": "(\w+)"\}', match_text)
        if query_type_match:
            query_type = query_type_match.group(1)
            fixed_replacement = replacement.replace("$QUERY_TYPE", query_type)
            content = content.replace(match_text, fixed_replacement)
    
    # Replace manual feature conversion with helper function
    manual_conversion_pattern = r"""# Convert extracted features to format needed by matching engine\s+
        matching_features = \{\}\s+
        for feature_name, feature_vector in features\.items\(\):\s+
            if "visual_cnn" in feature_name:\s+
                matching_features\[FeatureType\.CNN_FEATURES\.value\] = feature_vector\.vector\s+
            elif "visual_phash" in feature_name:\s+
                matching_features\[FeatureType\.PERCEPTUAL_HASH\.value\] = feature_vector\.vector\s+
            elif "visual_motion" in feature_name:\s+
                matching_features\[FeatureType\.MOTION_PATTERN\.value\] = feature_vector\.vector\s+
            elif "audio_fingerprint" in feature_name:\s+
                matching_features\[FeatureType\.AUDIO_SPECTROGRAM\.value\] = feature_vector\.vector"""
    
    conversion_replacement = """# Convert features to the format expected by the matching engine
        matching_features = prepare_matching_features(features)"""
    
    content = re.sub(manual_conversion_pattern, conversion_replacement, content)
    
    # Write the updated content back to the file
    with open(IDENTIFICATION_API_PATH, 'w') as f:
        f.write(content)
    
    print(f"Fixed direct vector database calls in {IDENTIFICATION_API_PATH}")
    return True


def update_feature_preparation_for_matching_engine():
    """Fix feature preparation for matching engine."""
    with open(IDENTIFICATION_API_PATH, 'r') as f:
        content = f.read()
    
    # Find all places where scene-based features are manually constructed
    scene_structure_pattern = r"""# Create scene structure for matching\s+
        video_scenes = \{\s+
            "scenes": \[\s+
                \{\s+
                    "start_time": 0\.0,\s+
                    "end_time": 0\.0,  # Will be updated during processing\s+
                    "features": matching_features\s+
                \}\s+
            \]\s+
        \}"""
    
    scene_structure_replacement = """# Prepare a proper video features structure with scenes
        video_features = {
            "scenes": [
                {
                    "start_time": 0.0,
                    "end_time": 10.0,  # Default duration estimate
                    "features": matching_features
                }
            ]
        }"""
    
    content = re.sub(scene_structure_pattern, scene_structure_replacement, content)
    
    # Update match_video calls to use the correct variable name and parameters
    match_video_pattern = r"""results = await matching_engine\.match_video\(\s+
            video_scenes,\s+
            matching_algorithms=\[MatchingAlgorithm\(algo\) for algo in params\.algorithms\],\s+
            max_results=params\.max_results,\s+
            threshold=params\.threshold\s+
        \)"""
    
    match_video_replacement = """results = await matching_engine.match_video(
            video_features,
            algorithms=[MatchingAlgorithm(algo) for algo in params.algorithms],
            top_k=params.max_results
        )"""
    
    content = re.sub(match_video_pattern, match_video_replacement, content)
    
    # Write the updated content back to the file
    with open(IDENTIFICATION_API_PATH, 'w') as f:
        f.write(content)
    
    print(f"Updated feature preparation for matching engine in {IDENTIFICATION_API_PATH}")
    return True


def main():
    """Main function."""
    # Fix direct vector database calls
    fix_direct_vector_db_calls()
    
    # Update feature preparation for matching engine
    update_feature_preparation_for_matching_engine()
    
    print("All fixes applied successfully!")


if __name__ == "__main__":
    main()
