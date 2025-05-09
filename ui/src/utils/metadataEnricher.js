/**
 * Metadata Enrichment Utility
 * Provides helper functions for enriching and formatting metadata
 */

import { metadataAPI } from '../services/api';

/**
 * Source priority order for different types of metadata
 * Higher priority sources will override lower priority ones
 */
const SOURCE_PRIORITIES = {
  title: ['tmdb', 'imdb', 'youtube', 'vimeo', 'spotify', 'internal'],
  description: ['tmdb', 'wikipedia', 'imdb', 'youtube', 'vimeo', 'internal'],
  images: ['tmdb', 'imdb', 'youtube', 'vimeo', 'internal'],
  cast: ['tmdb', 'imdb', 'internal'],
  release_date: ['tmdb', 'imdb', 'youtube', 'internal'],
  genre: ['tmdb', 'imdb', 'spotify', 'internal'],
  default: ['tmdb', 'imdb', 'youtube', 'vimeo', 'spotify', 'wikipedia', 'internal']
};

/**
 * Format fields that need special handling
 */
const FIELD_FORMATTERS = {
  // Duration formatting from seconds to HH:MM:SS
  duration: (seconds) => {
    if (!seconds && seconds !== 0) return 'Unknown';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    return hours > 0 
      ? `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}` 
      : `${minutes}:${secs.toString().padStart(2, '0')}`;
  },
  
  // Format runtime from minutes to hours and minutes
  runtime: (minutes) => {
    if (!minutes) return 'Unknown';
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;
  },
  
  // Format file size to human readable format
  file_size: (bytes) => {
    if (!bytes) return 'Unknown';
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    if (bytes === 0) return '0 Bytes';
    const i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)));
    return Math.round(bytes / Math.pow(1024, i), 2) + ' ' + sizes[i];
  },
  
  // Format rating to be out of 10
  vote_average: (rating) => {
    if (!rating) return 'No rating';
    return `${rating}/10`;
  },
  
  // Format timestamp for video matching
  timestamp: (seconds) => {
    if (!seconds && seconds !== 0) return 'Unknown';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }
};

/**
 * Get best value for a field from all sources based on priority
 * @param {Object} metadata - Combined metadata object from all sources
 * @param {string} field - Field name to get the best value for
 * @returns {any} Best value for the field
 */
export const getBestValue = (metadata, field) => {
  if (!metadata) return undefined;
  
  // Get the appropriate priority list for this field
  const priorities = SOURCE_PRIORITIES[field] || SOURCE_PRIORITIES.default;
  
  // Try each source in priority order
  for (const source of priorities) {
    if (metadata[source] && metadata[source][field] !== undefined && metadata[source][field] !== null) {
      return metadata[source][field];
    }
  }
  
  return undefined;
};

/**
 * Format a metadata field according to its type
 * @param {string} field - Name of the field
 * @param {any} value - Value to format
 * @returns {string} Formatted value
 */
export const formatField = (field, value) => {
  // Skip if value is undefined or null
  if (value === undefined || value === null) return null;
  
  // Apply formatter if exists for this field
  if (FIELD_FORMATTERS[field]) {
    return FIELD_FORMATTERS[field](value);
  }
  
  // Return arrays and objects as is (will be processed by UI component)
  if (Array.isArray(value) || typeof value === 'object') {
    return value;
  }
  
  // Return other values as strings
  return String(value);
};

/**
 * Combine metadata from multiple sources into a coherent object
 * @param {Object} metadata - Raw metadata from all sources
 * @param {Array} fields - List of fields to extract
 * @returns {Object} Enriched metadata
 */
export const combineMetadata = (metadata, fields = null) => {
  if (!metadata) return { _sources: {} };
  
  // Field mappings for different sources
  const fieldMappings = {
    tmdb: {
      overview: 'description'
    },
    imdb: {
      plot: 'description'
    },
    wikipedia: {
      url: 'wikipedia_url'
    }
  };
  
  // Get all available fields if not specified
  if (!fields) {
    fields = new Set();
    Object.keys(metadata).forEach(source => {
      if (metadata[source] && typeof metadata[source] === 'object') {
        Object.keys(metadata[source]).forEach(field => {
          // Add the original field name
          fields.add(field);
          
          // Also add any mapped field names
          if (fieldMappings[source] && fieldMappings[source][field]) {
            fields.add(fieldMappings[source][field]);
          }
        });
      }
    });
    fields = Array.from(fields);
  }
  
  // Combine fields from all sources based on priority
  const result = { _sources: {} };
  
  // Process standard fields
  fields.forEach(field => {
    const value = getBestValue(metadata, field);
    if (value !== undefined && value !== null) {
      result[field] = formatField(field, value);
      
      // Find which source provided this value
      const priorities = SOURCE_PRIORITIES[field] || SOURCE_PRIORITIES.default;
      for (const source of priorities) {
        if (metadata[source] && metadata[source][field] !== undefined && metadata[source][field] !== null) {
          result._sources[field] = source;
          break;
        }
      }
    }
  });
  
  // Process mapped fields
  Object.keys(fieldMappings).forEach(source => {
    if (metadata[source]) {
      Object.keys(fieldMappings[source]).forEach(originalField => {
        const mappedField = fieldMappings[source][originalField];
        // Only process if the result doesn't already have this field
        if (!result[mappedField] && metadata[source][originalField] !== undefined) {
          result[mappedField] = formatField(mappedField, metadata[source][originalField]);
          result._sources[mappedField] = source;
        }
      });
    }
  });
  
  return result;
};

/**
 * Get enriched metadata for a content ID
 * @param {string} contentId - Content ID to get metadata for
 * @param {Array} sources - Optional array of sources to request
 * @param {boolean} forceRefresh - Whether to force refresh from API
 * @param {Function} setCombined - Optional state setter for combined metadata
 * @returns {Promise<Object>} Combined metadata
 */
export const getEnrichedMetadata = async (contentId, sources = null, forceRefresh = false, setCombined = null) => {
  try {
    // Call API to get enriched metadata
    const response = await metadataAPI.getEnriched(contentId, sources);
    const rawMetadata = response.data;
    
    // Combine metadata from all sources
    const combined = combineMetadata(rawMetadata);
    
    // Update state if setter provided
    if (setCombined && typeof setCombined === 'function') {
      setCombined(combined);
    }
    
    return combined;
  } catch (error) {
    console.error('Error getting enriched metadata:', error);
    return null;
  }
};

/**
 * Filter metadata fields based on user permission
 * @param {Object} metadata - Combined metadata
 * @param {string} permission - User permission level
 * @returns {Object} Filtered metadata
 */
export const filterMetadataByPermission = (metadata, permission = 'public') => {
  if (!metadata) return {};
  
  // Define permission levels and sections
  const permissionLevels = ['guest', 'public', 'user', 'premium', 'admin'];
  
  // Handle 'guest' as equivalent to 'public' for backward compatibility
  const effectivePermission = permission === 'guest' ? 'public' : permission;
  const permissionRank = permissionLevels.indexOf(effectivePermission);
  
  // If invalid permission or admin, return all
  if (permissionRank < 0) return metadata;
  if (permission === 'admin') return metadata;
  
  // Define section visibility for different permission levels
  const sectionPermissions = {
    // Sections available to public users (guests)
    public: ['basic'],
    // Sections available to regular users
    user: ['basic', 'details', 'cast'],
    // Sections available to premium users
    premium: ['basic', 'details', 'cast', 'technical']
  };

  // Get allowed sections for this permission level
  let allowedSections = [];
  for (let i = 0; i <= permissionRank; i++) {
    const level = permissionLevels[i];
    if (sectionPermissions[level]) {
      allowedSections = [...allowedSections, ...sectionPermissions[level]];
    }
  }
  
  // Create a filtered copy of metadata with only allowed sections
  const filtered = {};
  
  // Handle standard format metadata (flat object with fields)
  if (!metadata.basic && !metadata.technical) {
    // Define field permissions (which fields are available at which level)
    const fieldPermissions = {
      // Public fields available to everyone
      public: [
        'title', 'overview', 'description', 'thumbnail_url', 'poster_url',
        'release_date', 'duration', 'genres', 'vote_average', 'content_id'
      ],
      // Basic user fields
      user: [
        'directors', 'cast', 'backdrop_url', 'trailer_url', 'tags',
        'keywords', 'runtime', 'language', 'timestamp', 'source_url'
      ],
      // Premium user fields
      premium: [
        'filming_locations', 'soundtrack', 'wikipedia_extract', 'imdb_id',
        'tmdb_id', 'budget', 'revenue', 'production_companies', 'streaming_services',
        'availability', 'similar_titles', 'media_type', 'collections'
      ]
    };
    
    // Get all allowed fields for this permission level
    let allowedFields = [];
    for (let i = 0; i <= permissionRank; i++) {
      const level = permissionLevels[i];
      if (fieldPermissions[level]) {
        allowedFields = [...allowedFields, ...fieldPermissions[level]];
      }
    }
    
    // Filter metadata object to only include allowed fields
    Object.keys(metadata).forEach(key => {
      if (key.startsWith('_')) {
        // Always include metadata fields starting with underscore (e.g. _sources)
        filtered[key] = metadata[key];
      } else if (allowedFields.includes(key)) {
        // Include fields that are allowed for this permission level
        filtered[key] = metadata[key];
      }
    });
  }
  // Handle formatted metadata (with sections like basic, technical, etc.)
  else {
    // Include only sections allowed for this permission level
    Object.keys(metadata).forEach(section => {
      if (allowedSections.includes(section) || section.startsWith('_')) {
        filtered[section] = metadata[section];
      }
    });
    
    // Make sure non-allowed sections are completely undefined, not empty arrays
    if (!allowedSections.includes('technical')) {
      filtered.technical = undefined;
    }
  }
  
  return filtered;
};

// Export all necessary functions and constants
export {
  getEnrichedMetadata as fetchMetadata,
  combineMetadata as enrichMetadata,
  FIELD_FORMATTERS,
  SOURCE_PRIORITIES
};
