import React, { useEffect, useState, useContext } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  Image,
  ActivityIndicator,
  RefreshControl,
  Alert
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';
import { AuthContext } from '../services/AuthContext';
import ApiService from '../services/ApiService';
import { format, isToday, isYesterday, parseISO } from 'date-fns';

const HistoryScreen = () => {
  const [history, setHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedFilter, setSelectedFilter] = useState('all');
  const { user } = useContext(AuthContext);
  const navigation = useNavigation();

  useEffect(() => {
    fetchHistory();
  }, [selectedFilter]);

  const fetchHistory = async () => {
    if (refreshing) return;
    
    try {
      setIsLoading(true);
      // In a real app, this would call your API with the selected filter
      const response = await ApiService.getUserHistory(user?.id, selectedFilter);
      
      // For demo purposes, we'll create some mock data
      const mockData = [
        {
          id: '1',
          timestamp: new Date(2025, 4, 7, 10, 30).toISOString(),
          videoTitle: 'Stranger Things Season 4',
          videoSource: 'Netflix',
          videoType: 'TV Show',
          confidence: 0.98,
          thumbnail: 'https://via.placeholder.com/300x169?text=Stranger+Things',
          duration: '00:45',
          saved: true
        },
        {
          id: '2',
          timestamp: new Date(2025, 4, 7, 9, 15).toISOString(),
          videoTitle: 'The Batman',
          videoSource: 'HBO Max',
          videoType: 'Movie',
          confidence: 0.95,
          thumbnail: 'https://via.placeholder.com/300x169?text=The+Batman',
          duration: '02:56',
          saved: false
        },
        {
          id: '3',
          timestamp: new Date(2025, 4, 6, 18, 22).toISOString(),
          videoTitle: 'Friends - The One with the Wedding',
          videoSource: 'Comedy Central',
          videoType: 'TV Show',
          confidence: 0.92,
          thumbnail: 'https://via.placeholder.com/300x169?text=Friends',
          duration: '00:22',
          saved: true
        },
        {
          id: '4',
          timestamp: new Date(2025, 4, 5, 20, 10).toISOString(),
          videoTitle: 'Formula 1: Drive to Survive',
          videoSource: 'Netflix',
          videoType: 'Documentary',
          confidence: 0.89,
          thumbnail: 'https://via.placeholder.com/300x169?text=Formula+1',
          duration: '00:50',
          saved: false
        },
        {
          id: '5',
          timestamp: new Date(2025, 4, 3, 14, 45).toISOString(),
          videoTitle: 'Game of Thrones - Battle of Winterfell',
          videoSource: 'HBO',
          videoType: 'TV Show',
          confidence: 0.97,
          thumbnail: 'https://via.placeholder.com/300x169?text=Game+of+Thrones',
          duration: '01:22',
          saved: true
        },
      ];
      
      // Filter based on selection
      let filteredData = mockData;
      if (selectedFilter === 'saved') {
        filteredData = mockData.filter(item => item.saved);
      }
      
      setHistory(filteredData);
    } catch (error) {
      console.error('Error fetching history:', error);
      Alert.alert('Error', 'Failed to load your identification history');
    } finally {
      setIsLoading(false);
      setRefreshing(false);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    fetchHistory();
  };

  const handleFilterChange = (filter) => {
    setSelectedFilter(filter);
  };

  const formatDate = (timestamp) => {
    const date = parseISO(timestamp);
    if (isToday(date)) {
      return `Today at ${format(date, 'h:mm a')}`;
    } else if (isYesterday(date)) {
      return `Yesterday at ${format(date, 'h:mm a')}`;
    } else {
      return format(date, 'MMM d, yyyy \\at h:mm a');
    }
  };

  const handleItemPress = (item) => {
    navigation.navigate('ResultScreen', { result: item });
  };

  const toggleSaved = (id) => {
    setHistory(prevHistory =>
      prevHistory.map(item =>
        item.id === id ? { ...item, saved: !item.saved } : item
      )
    );
  };

  const EmptyListComponent = () => (
    <View style={styles.emptyContainer}>
      <Ionicons name="time-outline" size={80} color="#ccc" />
      <Text style={styles.emptyTitle}>
        {selectedFilter === 'all' ? 'No history yet' : 'No saved identifications'}
      </Text>
      <Text style={styles.emptyText}>
        {selectedFilter === 'all'
          ? 'Your video identifications will appear here'
          : 'Save your favorite identifications to find them here'}
      </Text>
      <TouchableOpacity
        style={styles.identifyButton}
        onPress={() => navigation.navigate('VideoIdentifyScreen')}
      >
        <Text style={styles.identifyButtonText}>Identify a Video</Text>
      </TouchableOpacity>
    </View>
  );

  const renderItem = ({ item }) => (
    <TouchableOpacity
      style={styles.historyItem}
      onPress={() => handleItemPress(item)}
    >
      <Image
        source={{ uri: item.thumbnail }}
        style={styles.thumbnail}
        resizeMode="cover"
      />
      <View style={styles.itemContent}>
        <View style={styles.itemHeader}>
          <Text style={styles.videoTitle} numberOfLines={1}>{item.videoTitle}</Text>
          <TouchableOpacity onPress={() => toggleSaved(item.id)}>
            <Ionicons
              name={item.saved ? 'bookmark' : 'bookmark-outline'}
              size={22}
              color={item.saved ? '#6a11cb' : '#888'}
            />
          </TouchableOpacity>
        </View>
        <Text style={styles.videoInfo}>{item.videoSource} • {item.videoType}</Text>
        <View style={styles.detailRow}>
          <View style={styles.confidenceContainer}>
            <Text style={styles.confidenceLabel}>Match:</Text>
            <Text style={styles.confidenceValue}>{Math.round(item.confidence * 100)}%</Text>
          </View>
          <Text style={styles.duration}>{item.duration}</Text>
        </View>
        <Text style={styles.timestamp}>{formatDate(item.timestamp)}</Text>
      </View>
    </TouchableOpacity>
  );

  const renderSectionHeader = (date) => {
    const formattedDate = format(parseISO(date), 'EEEE, MMMM d, yyyy');
    return (
      <View style={styles.sectionHeader}>
        <Text style={styles.sectionHeaderText}>{formattedDate}</Text>
      </View>
    );
  };

  // Group items by date for section headers
  const groupedData = () => {
    const groups = {};
    history.forEach(item => {
      const date = item.timestamp.split('T')[0]; // Get just the date part
      if (!groups[date]) {
        groups[date] = [];
      }
      groups[date].push(item);
    });
    
    // Convert to array format for SectionList
    const result = Object.keys(groups).sort().reverse().map(date => ({
      date,
      data: groups[date]
    }));
    
    return result;
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Identification History</Text>
      </View>
      
      <View style={styles.filterContainer}>
        <TouchableOpacity
          style={[styles.filterButton, selectedFilter === 'all' && styles.activeFilterButton]}
          onPress={() => handleFilterChange('all')}
        >
          <Text
            style={[styles.filterText, selectedFilter === 'all' && styles.activeFilterText]}
          >
            All
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.filterButton, selectedFilter === 'saved' && styles.activeFilterButton]}
          onPress={() => handleFilterChange('saved')}
        >
          <Text
            style={[styles.filterText, selectedFilter === 'saved' && styles.activeFilterText]}
          >
            Saved
          </Text>
        </TouchableOpacity>
      </View>

      {isLoading && !refreshing ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#6a11cb" />
          <Text style={styles.loadingText}>Loading your history...</Text>
        </View>
      ) : (
        <FlatList
          data={history}
          renderItem={renderItem}
          keyExtractor={item => item.id}
          contentContainerStyle={styles.listContent}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={onRefresh}
              colors={['#6a11cb', '#2575fc']}
              tintColor="#6a11cb"
            />
          }
          ListEmptyComponent={EmptyListComponent}
          ItemSeparatorComponent={() => <View style={styles.separator} />}
        />
      )}
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f8f8',
  },
  header: {
    backgroundColor: '#fff',
    padding: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#eeeeee',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
  },
  filterContainer: {
    flexDirection: 'row',
    padding: 10,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#eeeeee',
  },
  filterButton: {
    paddingVertical: 8,
    paddingHorizontal: 20,
    borderRadius: 20,
    marginRight: 10,
  },
  activeFilterButton: {
    backgroundColor: '#6a11cb',
  },
  filterText: {
    fontSize: 14,
    color: '#666',
    fontWeight: '500',
  },
  activeFilterText: {
    color: '#fff',
    fontWeight: 'bold',
  },
  listContent: {
    padding: 15,
    paddingTop: 10,
  },
  loadingContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  loadingText: {
    marginTop: 10,
    color: '#666',
    fontSize: 16,
  },
  historyItem: {
    backgroundColor: '#fff',
    borderRadius: 10,
    overflow: 'hidden',
    marginBottom: 15,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 5,
    elevation: 3,
  },
  thumbnail: {
    width: '100%',
    height: 150,
    backgroundColor: '#eee',
  },
  itemContent: {
    padding: 12,
  },
  itemHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  videoTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    flex: 1,
    marginRight: 10,
  },
  videoInfo: {
    fontSize: 14,
    color: '#666',
    marginBottom: 8,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 5,
  },
  confidenceContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  confidenceLabel: {
    fontSize: 14,
    color: '#666',
    marginRight: 5,
  },
  confidenceValue: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#6a11cb',
  },
  duration: {
    fontSize: 13,
    color: '#888',
  },
  timestamp: {
    fontSize: 12,
    color: '#999',
    marginTop: 2,
  },
  separator: {
    height: 15,
  },
  sectionHeader: {
    backgroundColor: '#f8f8f8',
    padding: 10,
    marginVertical: 5,
    borderRadius: 5,
  },
  sectionHeaderText: {
    fontWeight: 'bold',
    color: '#666',
  },
  emptyContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 50,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#555',
    marginTop: 20,
    marginBottom: 10,
  },
  emptyText: {
    fontSize: 14,
    color: '#888',
    textAlign: 'center',
    marginBottom: 30,
    paddingHorizontal: 30,
  },
  identifyButton: {
    backgroundColor: '#6a11cb',
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 25,
  },
  identifyButtonText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 16,
  },
});

export default HistoryScreen;
