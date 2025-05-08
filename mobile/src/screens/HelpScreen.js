import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Alert,
  ActivityIndicator,
  Linking
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import { Ionicons, MaterialIcons } from '@expo/vector-icons';

const HelpScreen = () => {
  const navigation = useNavigation();
  const [expandedFaq, setExpandedFaq] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState('');

  const faqs = [
    {
      id: 1,
      question: 'How does VidID work?',
      answer: 'VidID uses advanced computer vision and machine learning algorithms to analyze video content. When you submit a clip, our system extracts visual features, motion patterns, and audio characteristics, then matches them against our database of millions of videos to identify the source content.'
    },
    {
      id: 2,
      question: 'What types of videos can VidID identify?',
      answer: 'VidID can identify movies, TV shows, streaming content, YouTube videos, commercials, music videos, and more. Our database includes content from major streaming platforms like Netflix, Amazon Prime, Disney+, as well as broadcast television and popular online videos.'
    },
    {
      id: 3,
      question: 'How long does the video clip need to be?',
      answer: 'For best results, we recommend submitting a clip that is at least 5-10 seconds long. The longer the clip, the more accurate the identification may be. However, VidID can often identify content from clips as short as 3 seconds if they contain distinctive visual or audio elements.'
    },
    {
      id: 4,
      question: 'Why couldn\'t VidID identify my video?',
      answer: 'There could be several reasons: the video may not be in our database yet, the clip might be too short or of poor quality, or it might contain heavy modifications like filters, text overlays, or significant cropping that alter the visual features. Try submitting a longer or clearer clip if possible.'
    },
    {
      id: 5,
      question: 'Is my data private?',
      answer: 'Yes, we take privacy seriously. The video clips you submit are only used for the purpose of identification and are not permanently stored without your consent. You can control your privacy settings in the app to determine how your data is handled.'
    },
    {
      id: 6,
      question: 'How often is the database updated?',
      answer: 'Our database is continuously updated to include new releases from streaming platforms, television broadcasts, and online sources. Major content is typically added within 24-48 hours of release.'
    },
    {
      id: 7,
      question: 'Do I need an internet connection to use VidID?',
      answer: 'Yes, VidID requires an internet connection to process your video clip and match it against our database. The app cannot perform identifications offline.'
    },
    {
      id: 8,
      question: 'How accurate is VidID?',
      answer: 'VidID achieves over 95% accuracy for content in our database when provided with good quality clips. Factors like video quality, clip length, and visual distinctiveness affect accuracy. Each result includes a confidence score to indicate match reliability.'
    },
    {
      id: 9,
      question: 'Can I identify videos from my photo library?',
      answer: 'Yes, you can upload videos from your device\'s photo library for identification. Simply tap the "Gallery" button on the video identification screen and select the video you want to identify.'
    },
    {
      id: 10,
      question: 'Is there a limit to how many videos I can identify?',
      answer: 'Free accounts can identify up to 10 videos per day. Premium subscribers enjoy unlimited identifications and additional features.'
    },
  ];

  const toggleFaq = (id) => {
    if (expandedFaq === id) {
      setExpandedFaq(null);
    } else {
      setExpandedFaq(id);
    }
  };

  const filteredFaqs = faqs.filter(faq =>
    faq.question.toLowerCase().includes(searchQuery.toLowerCase()) ||
    faq.answer.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleSubmitQuery = () => {
    if (!message.trim()) {
      Alert.alert('Error', 'Please enter your question or issue');
      return;
    }

    setIsLoading(true);
    
    // Simulate API call
    setTimeout(() => {
      setIsLoading(false);
      Alert.alert(
        'Query Submitted',
        'Thank you for contacting us. We\'ve received your message and will get back to you as soon as possible.',
        [{ text: 'OK', onPress: () => setMessage('') }]
      );
    }, 1500);
  };

  const contactSupport = (method) => {
    switch (method) {
      case 'email':
        Linking.openURL('mailto:support@vidid.com?subject=VidID%20Support%20Request');
        break;
      case 'chat':
        Alert.alert('Live Chat', 'Live chat support is available from 9 AM to 8 PM EST. Would you like to start a chat session?', [
          { text: 'Cancel', style: 'cancel' },
          { text: 'Start Chat', onPress: () => Alert.alert('Chat Initiated', 'Connecting to a support agent...') }
        ]);
        break;
      case 'phone':
        Linking.openURL('tel:+18005551234');
        break;
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
          <Ionicons name="arrow-back" size={24} color="#333" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Help & Support</Text>
        <View style={styles.backButtonPlaceholder} />
      </View>

      <ScrollView style={styles.scrollView}>
        {/* Support Options */}
        <View style={styles.supportOptionsContainer}>
          <Text style={styles.sectionTitle}>Contact Us</Text>
          
          <View style={styles.supportOptionsRow}>
            <TouchableOpacity 
              style={styles.supportOption} 
              onPress={() => contactSupport('email')}
            >
              <View style={[styles.supportIconContainer, { backgroundColor: '#2575fc' }]}>
                <Ionicons name="mail-outline" size={24} color="#fff" />
              </View>
              <Text style={styles.supportOptionLabel}>Email</Text>
            </TouchableOpacity>
            
            <TouchableOpacity 
              style={styles.supportOption} 
              onPress={() => contactSupport('chat')}
            >
              <View style={[styles.supportIconContainer, { backgroundColor: '#6a11cb' }]}>
                <Ionicons name="chatbubbles-outline" size={24} color="#fff" />
              </View>
              <Text style={styles.supportOptionLabel}>Live Chat</Text>
            </TouchableOpacity>
            
            <TouchableOpacity 
              style={styles.supportOption} 
              onPress={() => contactSupport('phone')}
            >
              <View style={[styles.supportIconContainer, { backgroundColor: '#4caf50' }]}>
                <Ionicons name="call-outline" size={24} color="#fff" />
              </View>
              <Text style={styles.supportOptionLabel}>Call Us</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Search FAQs */}
        <View style={styles.searchContainer}>
          <View style={styles.searchBar}>
            <Ionicons name="search" size={20} color="#999" style={styles.searchIcon} />
            <TextInput
              style={styles.searchInput}
              placeholder="Search frequently asked questions"
              value={searchQuery}
              onChangeText={setSearchQuery}
              clearButtonMode="while-editing"
            />
            {searchQuery ? (
              <TouchableOpacity onPress={() => setSearchQuery('')} style={styles.clearButton}>
                <Ionicons name="close-circle" size={18} color="#999" />
              </TouchableOpacity>
            ) : null}
          </View>
        </View>

        {/* Frequently Asked Questions */}
        <View style={styles.faqContainer}>
          <Text style={styles.sectionTitle}>Frequently Asked Questions</Text>
          
          {filteredFaqs.length > 0 ? (
            filteredFaqs.map(faq => (
              <TouchableOpacity
                key={faq.id}
                style={styles.faqItem}
                onPress={() => toggleFaq(faq.id)}
                activeOpacity={0.7}
              >
                <View style={styles.faqQuestion}>
                  <Text style={styles.faqQuestionText}>{faq.question}</Text>
                  <Ionicons
                    name={expandedFaq === faq.id ? 'chevron-up' : 'chevron-down'}
                    size={22}
                    color="#6a11cb"
                  />
                </View>
                {expandedFaq === faq.id && (
                  <View style={styles.faqAnswer}>
                    <Text style={styles.faqAnswerText}>{faq.answer}</Text>
                  </View>
                )}
              </TouchableOpacity>
            ))
          ) : (
            <View style={styles.noResultsContainer}>
              <Ionicons name="search-outline" size={48} color="#ccc" />
              <Text style={styles.noResultsText}>No matching FAQs found</Text>
              <Text style={styles.noResultsSubtext}>Try using different keywords or ask us directly</Text>
            </View>
          )}
        </View>

        {/* Ask a Question */}
        <View style={styles.askQuestionContainer}>
          <Text style={styles.sectionTitle}>Still Have Questions?</Text>
          <Text style={styles.askQuestionSubtitle}>Send us your question and we'll get back to you as soon as possible</Text>
          
          <TextInput
            style={styles.messageInput}
            placeholder="Type your question or describe your issue"
            value={message}
            onChangeText={setMessage}
            multiline
            numberOfLines={5}
            textAlignVertical="top"
          />
          
          <TouchableOpacity
            style={styles.submitButton}
            onPress={handleSubmitQuery}
            disabled={isLoading}
          >
            {isLoading ? (
              <ActivityIndicator size="small" color="#fff" />
            ) : (
              <Text style={styles.submitButtonText}>Submit</Text>
            )}
          </TouchableOpacity>
        </View>

        {/* Help Topics */}
        <View style={styles.helpTopicsContainer}>
          <Text style={styles.sectionTitle}>Help Topics</Text>
          
          <TouchableOpacity 
            style={styles.helpTopic}
            onPress={() => navigation.navigate('GettingStarted')}
          >
            <Ionicons name="rocket-outline" size={24} color="#6a11cb" style={styles.helpTopicIcon} />
            <View style={styles.helpTopicContent}>
              <Text style={styles.helpTopicTitle}>Getting Started</Text>
              <Text style={styles.helpTopicDescription}>New to VidID? Learn the basics</Text>
            </View>
            <Ionicons name="chevron-forward" size={22} color="#ccc" />
          </TouchableOpacity>
          
          <TouchableOpacity 
            style={styles.helpTopic}
            onPress={() => navigation.navigate('Troubleshooting')}
          >
            <Ionicons name="build-outline" size={24} color="#6a11cb" style={styles.helpTopicIcon} />
            <View style={styles.helpTopicContent}>
              <Text style={styles.helpTopicTitle}>Troubleshooting</Text>
              <Text style={styles.helpTopicDescription}>Solve common issues</Text>
            </View>
            <Ionicons name="chevron-forward" size={22} color="#ccc" />
          </TouchableOpacity>
          
          <TouchableOpacity 
            style={styles.helpTopic}
            onPress={() => navigation.navigate('AccountHelp')}
          >
            <Ionicons name="person-outline" size={24} color="#6a11cb" style={styles.helpTopicIcon} />
            <View style={styles.helpTopicContent}>
              <Text style={styles.helpTopicTitle}>Account & Billing</Text>
              <Text style={styles.helpTopicDescription}>Manage your account and subscription</Text>
            </View>
            <Ionicons name="chevron-forward" size={22} color="#ccc" />
          </TouchableOpacity>
          
          <TouchableOpacity 
            style={styles.helpTopic}
            onPress={() => navigation.navigate('PrivacySecurity')}
          >
            <Ionicons name="shield-outline" size={24} color="#6a11cb" style={styles.helpTopicIcon} />
            <View style={styles.helpTopicContent}>
              <Text style={styles.helpTopicTitle}>Privacy & Security</Text>
              <Text style={styles.helpTopicDescription}>Learn how we protect your data</Text>
            </View>
            <Ionicons name="chevron-forward" size={22} color="#ccc" />
          </TouchableOpacity>
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
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#fff',
    paddingHorizontal: 15,
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#eeeeee',
  },
  backButton: {
    padding: 5,
  },
  backButtonPlaceholder: {
    width: 34,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
  },
  scrollView: {
    flex: 1,
  },
  supportOptionsContainer: {
    backgroundColor: '#fff',
    padding: 20,
    marginBottom: 15,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 15,
  },
  supportOptionsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: 10,
  },
  supportOption: {
    alignItems: 'center',
    width: '30%',
  },
  supportIconContainer: {
    width: 60,
    height: 60,
    borderRadius: 30,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 8,
  },
  supportOptionLabel: {
    fontSize: 14,
    color: '#555',
    fontWeight: '500',
  },
  searchContainer: {
    backgroundColor: '#fff',
    paddingHorizontal: 20,
    paddingVertical: 15,
    marginBottom: 15,
  },
  searchBar: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#f2f2f2',
    borderRadius: 10,
    paddingHorizontal: 15,
  },
  searchIcon: {
    marginRight: 10,
  },
  searchInput: {
    flex: 1,
    height: 45,
    fontSize: 15,
    color: '#333',
  },
  clearButton: {
    padding: 5,
  },
  faqContainer: {
    backgroundColor: '#fff',
    padding: 20,
    marginBottom: 15,
  },
  faqItem: {
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
    paddingVertical: 15,
  },
  faqQuestion: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  faqQuestionText: {
    fontSize: 16,
    fontWeight: '500',
    color: '#333',
    flex: 1,
    marginRight: 10,
  },
  faqAnswer: {
    marginTop: 10,
    backgroundColor: '#f9f9f9',
    padding: 15,
    borderRadius: 8,
  },
  faqAnswerText: {
    fontSize: 15,
    color: '#555',
    lineHeight: 22,
  },
  noResultsContainer: {
    alignItems: 'center',
    padding: 20,
  },
  noResultsText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#555',
    marginTop: 15,
    marginBottom: 5,
  },
  noResultsSubtext: {
    fontSize: 14,
    color: '#888',
    textAlign: 'center',
  },
  askQuestionContainer: {
    backgroundColor: '#fff',
    padding: 20,
    marginBottom: 15,
  },
  askQuestionSubtitle: {
    fontSize: 14,
    color: '#777',
    marginBottom: 15,
  },
  messageInput: {
    backgroundColor: '#f9f9f9',
    borderWidth: 1,
    borderColor: '#eee',
    borderRadius: 10,
    padding: 15,
    fontSize: 15,
    color: '#333',
    marginBottom: 15,
    minHeight: 120,
  },
  submitButton: {
    backgroundColor: '#6a11cb',
    borderRadius: 10,
    paddingVertical: 15,
    alignItems: 'center',
  },
  submitButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  helpTopicsContainer: {
    backgroundColor: '#fff',
    padding: 20,
    marginBottom: 30,
  },
  helpTopic: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  helpTopicIcon: {
    marginRight: 15,
  },
  helpTopicContent: {
    flex: 1,
  },
  helpTopicTitle: {
    fontSize: 16,
    fontWeight: '500',
    color: '#333',
    marginBottom: 3,
  },
  helpTopicDescription: {
    fontSize: 14,
    color: '#777',
  },
});

export default HelpScreen;
