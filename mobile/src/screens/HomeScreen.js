import React, { useState, useContext, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Image,
  FlatList,
  Dimensions,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import { AuthContext } from '../services/AuthContext';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';

const { width } = Dimensions.get('window');
const cardWidth = width * 0.85;

const HomeScreen = () => {
  const navigation = useNavigation();
  const { state } = useContext(AuthContext);
  const [isLoading, setIsLoading] = useState(false);
  const [recentIdentifications, setRecentIdentifications] = useState([]);
  const [trendingVideos, setTrendingVideos] = useState([]);
  const [stats, setStats] = useState({
    totalIdentifications: 0,
    databaseSize: 0,
    videoRange: '',
  });

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    setIsLoading(true);
    
    try {
      // In a real app, these would be API calls
      // For demo purposes, we'll use mock data
      
      // Simulate API call delay
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Mock recent identifications
      setRecentIdentifications([
        {
          id: '1',
          title: 'Stranger Things Season 4',
          source: 'Netflix',
          timestamp: '2 hours ago',
          thumbnail: 'https://via.placeholder.com/300x169?text=Stranger+Things',
          confidence: 0.98,
        },
        {
          id: '2',
          title: 'The Batman',
          source: 'HBO Max',
          timestamp: 'Yesterday',
          thumbnail: 'https://via.placeholder.com/300x169?text=The+Batman',
          confidence: 0.95,
        },
        {
          id: '3',
          title: 'Friends - Season 5, Episode 8',
          source: 'Comedy Central',
          timestamp: '3 days ago',
          thumbnail: 'https://via.placeholder.com/300x169?text=Friends',
          confidence: 0.92,
        },
      ]);
      
      // Mock trending videos
      setTrendingVideos([
        {
          id: '1',
          title: 'Squid Game',
          source: 'Netflix',
          identifications: 4523,
          thumbnail: 'https://via.placeholder.com/300x169?text=Squid+Game',
        },
        {
          id: '2',
          title: 'House of the Dragon',
          source: 'HBO Max',
          identifications: 3897,
          thumbnail: 'https://via.placeholder.com/300x169?text=House+of+Dragon',
        },
        {
          id: '3',
          title: 'The Boys',
          source: 'Amazon Prime',
          identifications: 3254,
          thumbnail: 'https://via.placeholder.com/300x169?text=The+Boys',
        },
        {
          id: '4',
          title: 'Wednesday',
          source: 'Netflix',
          identifications: 2876,
          thumbnail: 'https://via.placeholder.com/300x169?text=Wednesday',
        },
      ]);
      
      // Mock stats
      setStats({
        totalIdentifications: 1356421,
        databaseSize: 1235789,
        videoRange: '1950 - 2025',
      });
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const formatNumber = (num) => {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K';
    }
    return num;
  };

  const handleIdentifyPress = () => {
    navigation.navigate('Identify');
  };

  const handleIdentificationPress = (item) => {
    navigation.navigate('Result', { result: item });
  };

  const renderRecentItem = ({ item }) => (
    <TouchableOpacity
      style={styles.recentItem}
      onPress={() => handleIdentificationPress(item)}
    >
      <Image source={{ uri: item.thumbnail }} style={styles.recentThumbnail} />
      <View style={styles.recentContent}>
        <Text style={styles.recentTitle} numberOfLines={1}>{item.title}</Text>
        <Text style={styles.recentSource}>{item.source}</Text>
        <View style={styles.recentMeta}>
          <Text style={styles.recentTime}>{item.timestamp}</Text>
          <View style={styles.confidenceContainer}>
            <Text style={styles.confidenceText}>
              {Math.round(item.confidence * 100)}% match
            </Text>
          </View>
        </View>
      </View>
    </TouchableOpacity>
  );

  const renderTrendingItem = ({ item }) => (
    <TouchableOpacity style={styles.trendingItem}>
      <Image source={{ uri: item.thumbnail }} style={styles.trendingThumbnail} />
      <View style={styles.trendingOverlay}>
        <Text style={styles.trendingTitle} numberOfLines={2}>{item.title}</Text>
        <Text style={styles.trendingSource}>{item.source}</Text>
        <View style={styles.trendingMeta}>
          <Ionicons name="eye-outline" size={14} color="#fff" />
          <Text style={styles.trendingCount}>{formatNumber(item.identifications)}</Text>
        </View>
      </View>
    </TouchableOpacity>
  );

  if (isLoading) {
    return (
      <SafeAreaView style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#6a11cb" />
        <Text style={styles.loadingText}>Loading dashboard...</Text>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Image 
          source={require('../../assets/vidid-logo.png')} 
          style={styles.logo}
          resizeMode="contain"
        />
        <Text style={styles.headerTitle}>VidID</Text>
      </View>

      <ScrollView style={styles.scrollView}>
        {/* Welcome Card */}
        <LinearGradient
          colors={['#6a11cb', '#2575fc']}
          style={styles.welcomeCard}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
        >
          <View style={styles.welcomeContent}>
            <Text style={styles.welcomeTitle}>
              Welcome{state.user ? `, ${state.user.name.split(' ')[0]}` : ''}!
            </Text>
            <Text style={styles.welcomeText}>
              Identify any movie or TV show from a short clip in seconds
            </Text>
            <TouchableOpacity 
              style={styles.identifyButton}
              onPress={handleIdentifyPress}
            >
              <Ionicons name="videocam" size={18} color="#fff" style={styles.buttonIcon} />
              <Text style={styles.identifyButtonText}>Identify Now</Text>
            </TouchableOpacity>
          </View>
          <View style={styles.welcomeImageContainer}>
            <Image 
              source={require('../../assets/vidid-logo.png')} 
              style={styles.welcomeImage}
              resizeMode="contain"
            />
          </View>
        </LinearGradient>

        {/* Stats Section */}
        <View style={styles.statsContainer}>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>{formatNumber(stats.totalIdentifications)}</Text>
            <Text style={styles.statLabel}>Identifications</Text>
          </View>
          <View style={styles.statDivider} />
          <View style={styles.statItem}>
            <Text style={styles.statValue}>{formatNumber(stats.databaseSize)}</Text>
            <Text style={styles.statLabel}>Videos in Database</Text>
          </View>
          <View style={styles.statDivider} />
          <View style={styles.statItem}>
            <Text style={styles.statValue}>{stats.videoRange}</Text>
            <Text style={styles.statLabel}>Year Range</Text>
          </View>
        </View>

        {/* Recent Identifications Section */}
        {recentIdentifications.length > 0 && (
          <View style={styles.section}>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>Recent Identifications</Text>
              <TouchableOpacity onPress={() => navigation.navigate('History')}>
                <Text style={styles.seeAllText}>See All</Text>
              </TouchableOpacity>
            </View>
            {recentIdentifications.map((item) => renderRecentItem({ item }))}
          </View>
        )}

        {/* Trending Videos Section */}
        {trendingVideos.length > 0 && (
          <View style={styles.section}>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>Trending Videos</Text>
              <TouchableOpacity>
                <Text style={styles.seeAllText}>See All</Text>
              </TouchableOpacity>
            </View>
            <FlatList
              data={trendingVideos}
              renderItem={renderTrendingItem}
              keyExtractor={(item) => item.id}
              horizontal
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={styles.trendingList}
            />
          </View>
        )}

        {/* How It Works Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>How It Works</Text>
          <View style={styles.howItWorksContainer}>
            <View style={styles.stepContainer}>
              <View style={styles.stepNumberContainer}>
                <Text style={styles.stepNumber}>1</Text>
              </View>
              <Text style={styles.stepTitle}>Capture</Text>
              <Text style={styles.stepDescription}>Record a short clip or upload from your gallery</Text>
            </View>
            
            <View style={styles.stepArrow}>
              <Ionicons name="arrow-forward" size={20} color="#999" />
            </View>
            
            <View style={styles.stepContainer}>
              <View style={styles.stepNumberContainer}>
                <Text style={styles.stepNumber}>2</Text>
              </View>
              <Text style={styles.stepTitle}>Process</Text>
              <Text style={styles.stepDescription}>Our AI analyzes visual and audio features</Text>
            </View>
            
            <View style={styles.stepArrow}>
              <Ionicons name="arrow-forward" size={20} color="#999" />
            </View>
            
            <View style={styles.stepContainer}>
              <View style={styles.stepNumberContainer}>
                <Text style={styles.stepNumber}>3</Text>
              </View>
              <Text style={styles.stepTitle}>Identify</Text>
              <Text style={styles.stepDescription}>Get instant results with detailed information</Text>
            </View>
          </View>
        </View>

        {/* Premium Banner */}
        <TouchableOpacity style={styles.premiumBanner}>
          <LinearGradient
            colors={['#FF8C00', '#FFA500']}
            style={styles.premiumGradient}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 0 }}
          >
            <View style={styles.premiumContent}>
              <Ionicons name="star" size={24} color="#fff" />
              <View style={styles.premiumTextContainer}>
                <Text style={styles.premiumTitle}>Upgrade to Premium</Text>
                <Text style={styles.premiumDescription}>Unlimited identifications, no ads, and more</Text>
              </View>
            </View>
            <Ionicons name="chevron-forward" size={24} color="#fff" />
          </LinearGradient>
        </TouchableOpacity>

        <View style={styles.footer}>
          <Text style={styles.footerText}>VidID v1.0.0</Text>
          <Text style={styles.footerText}>© 2025 VidID Technologies, Inc.</Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f8f8',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f8f8f8',
  },
  loadingText: {
    marginTop: 10,
    color: '#666',
    fontSize: 16,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    paddingHorizontal: 15,
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#eeeeee',
  },
  logo: {
    width: 30,
    height: 30,
    marginRight: 8,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#6a11cb',
  },
  scrollView: {
    flex: 1,
  },
  welcomeCard: {
    flexDirection: 'row',
    borderRadius: 15,
    margin: 15,
    marginTop: 20,
    padding: 20,
    overflow: 'hidden',
  },
  welcomeContent: {
    flex: 3,
  },
  welcomeTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 8,
  },
  welcomeText: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.9)',
    marginBottom: 15,
    lineHeight: 20,
  },
  identifyButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255,255,255,0.2)',
    paddingVertical: 8,
    paddingHorizontal: 15,
    borderRadius: 20,
    alignSelf: 'flex-start',
  },
  buttonIcon: {
    marginRight: 5,
  },
  identifyButtonText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 14,
  },
  welcomeImageContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  welcomeImage: {
    width: 70,
    height: 70,
    opacity: 0.9,
  },
  statsContainer: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    borderRadius: 10,
    margin: 15,
    marginTop: 5,
    padding: 15,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
    elevation: 2,
  },
  statItem: {
    flex: 1,
    alignItems: 'center',
  },
  statDivider: {
    width: 1,
    backgroundColor: '#eee',
    marginHorizontal: 10,
  },
  statValue: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 5,
  },
  statLabel: {
    fontSize: 12,
    color: '#777',
    textAlign: 'center',
  },
  section: {
    backgroundColor: '#fff',
    borderRadius: 10,
    margin: 15,
    marginTop: 5,
    padding: 15,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
    elevation: 2,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 15,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
  },
  seeAllText: {
    color: '#6a11cb',
    fontSize: 14,
  },
  recentItem: {
    flexDirection: 'row',
    marginBottom: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#f5f5f5',
    paddingBottom: 15,
  },
  recentThumbnail: {
    width: 100,
    height: 56,
    borderRadius: 5,
    backgroundColor: '#f0f0f0',
  },
  recentContent: {
    flex: 1,
    marginLeft: 12,
    justifyContent: 'space-between',
  },
  recentTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 4,
  },
  recentSource: {
    fontSize: 14,
    color: '#666',
    marginBottom: 5,
  },
  recentMeta: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  recentTime: {
    fontSize: 12,
    color: '#999',
  },
  confidenceContainer: {
    backgroundColor: 'rgba(106, 17, 203, 0.1)',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 10,
  },
  confidenceText: {
    fontSize: 12,
    color: '#6a11cb',
    fontWeight: '500',
  },
  trendingList: {
    paddingVertical: 5,
  },
  trendingItem: {
    width: 160,
    marginRight: 15,
    borderRadius: 10,
    overflow: 'hidden',
  },
  trendingThumbnail: {
    width: 160,
    height: 90,
    backgroundColor: '#f0f0f0',
  },
  trendingOverlay: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: 'rgba(0,0,0,0.7)',
    padding: 10,
  },
  trendingTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#fff',
    marginBottom: 3,
  },
  trendingSource: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.8)',
    marginBottom: 5,
  },
  trendingMeta: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  trendingCount: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.8)',
    marginLeft: 5,
  },
  howItWorksContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 10,
  },
  stepContainer: {
    alignItems: 'center',
    flex: 1,
  },
  stepNumberContainer: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#6a11cb',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 10,
  },
  stepNumber: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
  stepTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    marginBottom: 5,
    textAlign: 'center',
  },
  stepDescription: {
    fontSize: 12,
    color: '#777',
    textAlign: 'center',
    lineHeight: 16,
  },
  stepArrow: {
    marginHorizontal: 5,
  },
  premiumBanner: {
    margin: 15,
    marginTop: 5,
    borderRadius: 10,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3,
    elevation: 2,
  },
  premiumGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 20,
  },
  premiumContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  premiumTextContainer: {
    marginLeft: 10,
  },
  premiumTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
  },
  premiumDescription: {
    fontSize: 13,
    color: 'rgba(255,255,255,0.9)',
    marginTop: 2,
  },
  footer: {
    alignItems: 'center',
    marginVertical: 20,
  },
  footerText: {
    fontSize: 12,
    color: '#999',
    marginVertical: 2,
  },
});

export default HomeScreen;
