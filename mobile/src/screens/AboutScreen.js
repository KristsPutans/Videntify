import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Image,
  TouchableOpacity,
  Linking,
  Platform
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';

const AboutScreen = () => {
  const navigation = useNavigation();

  const openLink = (url) => {
    Linking.canOpenURL(url).then(supported => {
      if (supported) {
        Linking.openURL(url);
      } else {
        console.log(`Cannot open URL: ${url}`);
      }
    });
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
          <Ionicons name="arrow-back" size={24} color="#333" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>About VidID</Text>
        <View style={styles.backButtonPlaceholder} />
      </View>

      <ScrollView style={styles.scrollView}>
        <View style={styles.logoSection}>
          <LinearGradient
            colors={['#6a11cb', '#2575fc']}
            style={styles.gradientBackground}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
          >
            <Image
              source={require('../../assets/vidid-logo.png')}
              style={styles.logo}
              resizeMode="contain"
            />
            <Text style={styles.appName}>VidID</Text>
            <Text style={styles.tagline}>Identify Any Video in Seconds</Text>
            <View style={styles.versionContainer}>
              <Text style={styles.versionText}>Version 1.0.0 (Build 124)</Text>
            </View>
          </LinearGradient>
        </View>

        <View style={styles.contentSection}>
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>About VidID</Text>
            <Text style={styles.paragraph}>
              VidID is an advanced video identification system designed to help you identify movies, TV shows, and other video content from short clips. Using state-of-the-art computer vision and machine learning technology, VidID can match your video sample against a vast database of content to provide accurate results in seconds.
            </Text>
            <Text style={styles.paragraph}>
              Whether you're trying to remember that movie you saw years ago, identify a scene from a TV show, or discover the source of a viral clip, VidID makes the process fast and simple.
            </Text>
          </View>

          <View style={styles.section}>
            <Text style={styles.sectionTitle}>How It Works</Text>
            <View style={styles.howItWorksStep}>
              <View style={styles.stepNumberContainer}>
                <Text style={styles.stepNumber}>1</Text>
              </View>
              <View style={styles.stepContent}>
                <Text style={styles.stepTitle}>Capture</Text>
                <Text style={styles.stepDescription}>
                  Record a short clip of the video you want to identify, or select a video from your gallery.
                </Text>
              </View>
            </View>

            <View style={styles.howItWorksStep}>
              <View style={styles.stepNumberContainer}>
                <Text style={styles.stepNumber}>2</Text>
              </View>
              <View style={styles.stepContent}>
                <Text style={styles.stepTitle}>Process</Text>
                <Text style={styles.stepDescription}>
                  VidID analyzes the visual features, audio, and other characteristics of your clip.
                </Text>
              </View>
            </View>

            <View style={styles.howItWorksStep}>
              <View style={styles.stepNumberContainer}>
                <Text style={styles.stepNumber}>3</Text>
              </View>
              <View style={styles.stepContent}>
                <Text style={styles.stepTitle}>Match</Text>
                <Text style={styles.stepDescription}>
                  Our advanced algorithms match your clip against our extensive database of content.
                </Text>
              </View>
            </View>

            <View style={styles.howItWorksStep}>
              <View style={styles.stepNumberContainer}>
                <Text style={styles.stepNumber}>4</Text>
              </View>
              <View style={styles.stepContent}>
                <Text style={styles.stepTitle}>Discover</Text>
                <Text style={styles.stepDescription}>
                  Get detailed information about the identified video, including title, release date, cast, and where to watch it.
                </Text>
              </View>
            </View>
          </View>

          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Our Database</Text>
            <Text style={styles.paragraph}>
              VidID's database includes millions of movies, TV shows, music videos, and other content from various sources, including:
            </Text>
            <View style={styles.bulletPoints}>
              <View style={styles.bulletPoint}>
                <View style={styles.bullet} />
                <Text style={styles.bulletText}>Major streaming platforms (Netflix, Amazon Prime, Disney+, etc.)</Text>
              </View>
              <View style={styles.bulletPoint}>
                <View style={styles.bullet} />
                <Text style={styles.bulletText}>Television broadcasts from around the world</Text>
              </View>
              <View style={styles.bulletPoint}>
                <View style={styles.bullet} />
                <Text style={styles.bulletText}>Popular YouTube content and viral videos</Text>
              </View>
              <View style={styles.bulletPoint}>
                <View style={styles.bullet} />
                <Text style={styles.bulletText}>Classic and contemporary films and TV shows</Text>
              </View>
            </View>
            <Text style={styles.paragraph}>
              Our database is continuously updated to include the latest content, ensuring you always get the most accurate and up-to-date results.
            </Text>
          </View>

          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Our Team</Text>
            <Text style={styles.paragraph}>
              VidID was created by a team of passionate engineers, machine learning experts, and movie enthusiasts who wanted to make video identification accessible to everyone.
            </Text>
            <Text style={styles.paragraph}>
              Founded in 2024, our mission is to build the world's most comprehensive and accurate video identification system.
            </Text>
          </View>

          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Connect With Us</Text>
            <View style={styles.connectLinks}>
              <TouchableOpacity
                style={styles.connectLink}
                onPress={() => openLink('https://vidid.com')}
              >
                <Ionicons name="globe-outline" size={24} color="#6a11cb" />
                <Text style={styles.connectLinkText}>Website</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.connectLink}
                onPress={() => openLink('https://twitter.com/vidid')}
              >
                <Ionicons name="logo-twitter" size={24} color="#6a11cb" />
                <Text style={styles.connectLinkText}>Twitter</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.connectLink}
                onPress={() => openLink('https://instagram.com/vidid')}
              >
                <Ionicons name="logo-instagram" size={24} color="#6a11cb" />
                <Text style={styles.connectLinkText}>Instagram</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.connectLink}
                onPress={() => openLink('mailto:support@vidid.com')}
              >
                <Ionicons name="mail-outline" size={24} color="#6a11cb" />
                <Text style={styles.connectLinkText}>Email</Text>
              </TouchableOpacity>
            </View>
          </View>

          <View style={styles.legalSection}>
            <TouchableOpacity
              style={styles.legalLink}
              onPress={() => navigation.navigate('PrivacyPolicy')}
            >
              <Text style={styles.legalLinkText}>Privacy Policy</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.legalLink}
              onPress={() => navigation.navigate('TermsOfService')}
            >
              <Text style={styles.legalLinkText}>Terms of Service</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.legalLink}
              onPress={() => navigation.navigate('Licenses')}
            >
              <Text style={styles.legalLinkText}>Licenses</Text>
            </TouchableOpacity>
          </View>

          <View style={styles.copyrightSection}>
            <Text style={styles.copyrightText}>u00a9 2025 VidID Technologies, Inc.</Text>
            <Text style={styles.copyrightText}>All Rights Reserved</Text>
          </View>
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
  logoSection: {
    width: '100%',
  },
  gradientBackground: {
    alignItems: 'center',
    paddingVertical: 50,
    paddingHorizontal: 20,
  },
  logo: {
    width: 100,
    height: 100,
    marginBottom: 15,
  },
  appName: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 5,
  },
  tagline: {
    fontSize: 16,
    color: 'rgba(255,255,255,0.9)',
    marginBottom: 20,
  },
  versionContainer: {
    backgroundColor: 'rgba(255,255,255,0.2)',
    paddingHorizontal: 15,
    paddingVertical: 5,
    borderRadius: 15,
  },
  versionText: {
    color: '#fff',
    fontSize: 14,
  },
  contentSection: {
    padding: 20,
  },
  section: {
    backgroundColor: '#fff',
    borderRadius: 10,
    padding: 20,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 15,
  },
  paragraph: {
    fontSize: 15,
    lineHeight: 22,
    color: '#555',
    marginBottom: 15,
  },
  howItWorksStep: {
    flexDirection: 'row',
    marginBottom: 15,
  },
  stepNumberContainer: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#6a11cb',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 15,
    marginTop: 3,
  },
  stepNumber: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
  stepContent: {
    flex: 1,
  },
  stepTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 5,
  },
  stepDescription: {
    fontSize: 15,
    color: '#555',
    lineHeight: 20,
  },
  bulletPoints: {
    marginBottom: 15,
  },
  bulletPoint: {
    flexDirection: 'row',
    marginBottom: 10,
    alignItems: 'center',
  },
  bullet: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#6a11cb',
    marginRight: 10,
  },
  bulletText: {
    fontSize: 15,
    color: '#555',
    flex: 1,
  },
  connectLinks: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  connectLink: {
    width: '48%',
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(106, 17, 203, 0.1)',
    padding: 15,
    borderRadius: 10,
    marginBottom: 10,
  },
  connectLinkText: {
    marginLeft: 10,
    fontSize: 15,
    color: '#6a11cb',
    fontWeight: '500',
  },
  legalSection: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginBottom: 20,
  },
  legalLink: {
    marginHorizontal: 10,
  },
  legalLinkText: {
    color: '#555',
    fontSize: 14,
    textDecorationLine: 'underline',
  },
  copyrightSection: {
    alignItems: 'center',
    marginBottom: 20,
  },
  copyrightText: {
    color: '#888',
    fontSize: 12,
    lineHeight: 18,
  },
});

export default AboutScreen;
