/**
 * Result Screen
 * Displays the matches found from video identification
 */

import React from 'react';
import {
  View,
  Text,
  Image,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Linking,
  Share,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/MaterialIcons';

const ResultScreen = ({ route, navigation }) => {
  const { result } = route.params;
  const matches = result?.matches || [];
  const topMatch = matches.length > 0 ? matches[0] : null;
  
  // Open streaming service link
  const openStreamingLink = (url) => {
    Linking.canOpenURL(url).then(supported => {
      if (supported) {
        Linking.openURL(url);
      } else {
        console.log("Cannot open URL: " + url);
      }
    });
  };
  
  // Share result
  const shareResult = async () => {
    if (!topMatch) return;
    
    try {
      await Share.share({
        message: `I just identified "${topMatch.title}" using VidID! ${topMatch.streaming_services?.[0]?.url || ''}`,
        title: 'Video identified with VidID',
      });
    } catch (error) {
      console.log('Error sharing result:', error);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity 
          style={styles.backButton} 
          onPress={() => navigation.goBack()}
        >
          <Icon name="arrow-back" size={24} color="#000" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Identification Results</Text>
        <TouchableOpacity style={styles.shareButton} onPress={shareResult}>
          <Icon name="share" size={24} color="#4C6EF5" />
        </TouchableOpacity>
      </View>
      
      <ScrollView style={styles.scrollView}>
        {matches.length > 0 ? (
          <>
            {/* Top match */}
            <View style={styles.topMatchContainer}>
              <Image 
                source={topMatch.thumbnail 
                  ? { uri: `data:image/jpeg;base64,${topMatch.thumbnail}` }
                  : require('../../assets/placeholder.jpg')} 
                style={styles.topMatchImage} 
                resizeMode="cover"
              />
              <View style={styles.matchInfoOverlay}>
                <View style={styles.confidenceBadge}>
                  <Text style={styles.confidenceText}>
                    {Math.round(topMatch.confidence * 100)}% Match
                  </Text>
                </View>
              </View>
              <View style={styles.topMatchInfo}>
                <Text style={styles.topMatchTitle}>{topMatch.title}</Text>
                <Text style={styles.matchType}>{topMatch.match_type}</Text>
                {topMatch.timestamp && (
                  <Text style={styles.timestampText}>
                    Timestamp: {topMatch.formatted_timestamp}
                  </Text>
                )}
              </View>
              
              {/* Streaming services */}
              {topMatch.streaming_services && topMatch.streaming_services.length > 0 && (
                <View style={styles.streamingContainer}>
                  <Text style={styles.sectionTitle}>Watch on:</Text>
                  <View style={styles.streamingButtons}>
                    {topMatch.streaming_services.map((service, index) => (
                      <TouchableOpacity 
                        key={index}
                        style={styles.streamingButton}
                        onPress={() => openStreamingLink(service.url)}
                      >
                        <Text style={styles.streamingButtonText}>{service.name}</Text>
                        <Icon name="play-arrow" size={16} color="#FFFFFF" />
                      </TouchableOpacity>
                    ))}
                  </View>
                </View>
              )}
            </View>
            
            {/* Other matches */}
            {matches.length > 1 && (
              <View style={styles.otherMatchesContainer}>
                <Text style={styles.sectionTitle}>Other Possible Matches</Text>
                {matches.slice(1).map((match, index) => (
                  <View key={index} style={styles.otherMatchItem}>
                    <Image 
                      source={match.thumbnail 
                        ? { uri: `data:image/jpeg;base64,${match.thumbnail}` }
                        : require('../../assets/placeholder.jpg')} 
                      style={styles.otherMatchImage} 
                      resizeMode="cover"
                    />
                    <View style={styles.otherMatchInfo}>
                      <Text style={styles.otherMatchTitle}>{match.title}</Text>
                      <Text style={styles.otherMatchConfidence}>
                        {Math.round(match.confidence * 100)}% Match
                      </Text>
                    </View>
                  </View>
                ))}
              </View>
            )}
          </>
        ) : (
          // No matches found
          <View style={styles.noMatchesContainer}>
            <Icon name="sentiment-dissatisfied" size={64} color="#666" />
            <Text style={styles.noMatchesText}>No matches found</Text>
            <Text style={styles.noMatchesSubtext}>
              Try recording a different scene or make sure the video is clear
            </Text>
            <TouchableOpacity 
              style={styles.tryAgainButton}
              onPress={() => navigation.goBack()}
            >
              <Text style={styles.tryAgainButtonText}>Try Again</Text>
            </TouchableOpacity>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#EEEEEE',
  },
  backButton: {
    padding: 8,
  },
  headerTitle: {
    flex: 1,
    textAlign: 'center',
    fontSize: 18,
    fontWeight: '600',
    color: '#333333',
  },
  shareButton: {
    padding: 8,
  },
  scrollView: {
    flex: 1,
  },
  topMatchContainer: {
    margin: 16,
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
    overflow: 'hidden',
  },
  topMatchImage: {
    width: '100%',
    height: 200,
    backgroundColor: '#EEEEEE',
  },
  matchInfoOverlay: {
    position: 'absolute',
    top: 12,
    right: 12,
    flexDirection: 'row',
  },
  confidenceBadge: {
    backgroundColor: '#4C6EF5',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  confidenceText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: 'bold',
  },
  topMatchInfo: {
    padding: 16,
  },
  topMatchTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333333',
    marginBottom: 4,
  },
  matchType: {
    fontSize: 14,
    color: '#666666',
    marginBottom: 8,
    textTransform: 'capitalize',
  },
  timestampText: {
    fontSize: 14,
    color: '#666666',
    marginTop: 4,
  },
  streamingContainer: {
    borderTopWidth: 1,
    borderTopColor: '#EEEEEE',
    padding: 16,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333333',
    marginBottom: 12,
  },
  streamingButtons: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  streamingButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#4C6EF5',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 4,
    marginRight: 8,
    marginBottom: 8,
  },
  streamingButtonText: {
    color: '#FFFFFF',
    fontWeight: '500',
    marginRight: 4,
  },
  otherMatchesContainer: {
    margin: 16,
    marginTop: 0,
  },
  otherMatchItem: {
    flexDirection: 'row',
    backgroundColor: '#FFFFFF',
    borderRadius: 8,
    overflow: 'hidden',
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  otherMatchImage: {
    width: 80,
    height: 80,
    backgroundColor: '#EEEEEE',
  },
  otherMatchInfo: {
    flex: 1,
    padding: 12,
    justifyContent: 'center',
  },
  otherMatchTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333333',
    marginBottom: 4,
  },
  otherMatchConfidence: {
    fontSize: 14,
    color: '#666666',
  },
  noMatchesContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 32,
    marginTop: 100,
  },
  noMatchesText: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333333',
    marginTop: 16,
    marginBottom: 8,
  },
  noMatchesSubtext: {
    fontSize: 16,
    color: '#666666',
    textAlign: 'center',
    marginBottom: 24,
  },
  tryAgainButton: {
    backgroundColor: '#4C6EF5',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 6,
  },
  tryAgainButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
});

export default ResultScreen;
