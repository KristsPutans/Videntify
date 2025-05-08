import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';

const PrivacyPolicyScreen = () => {
  const navigation = useNavigation();

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
          <Ionicons name="arrow-back" size={24} color="#333" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Privacy Policy</Text>
        <View style={styles.backButtonPlaceholder} />
      </View>

      <ScrollView style={styles.scrollView}>
        <View style={styles.contentContainer}>
          <Text style={styles.lastUpdated}>Last Updated: May 1, 2025</Text>
          
          <Text style={styles.introduction}>
            VidID Technologies, Inc. ("VidID," "we," "our," or "us") is committed to protecting your privacy. This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you use our VidID mobile application and related services (collectively, the "Service").
          </Text>
          <Text style={styles.introduction}>
            Please read this Privacy Policy carefully. If you do not agree with the terms of this Privacy Policy, please do not access the Service.
          </Text>
          
          <Text style={styles.sectionTitle}>1. COLLECTION OF YOUR INFORMATION</Text>
          <Text style={styles.paragraph}>
            We may collect information about you in various ways. The information we may collect via the Service includes:
          </Text>
          
          <Text style={styles.subheading}>1.1 Personal Data</Text>
          <Text style={styles.paragraph}>
            Personally identifiable information, such as your name, email address, telephone number, and demographic information that you voluntarily give to us when you register with the Service or when you choose to participate in various activities related to the Service. You are under no obligation to provide us with personal information of any kind, however your refusal to do so may prevent you from using certain features of the Service.
          </Text>
          
          <Text style={styles.subheading}>1.2 Video Data</Text>
          <Text style={styles.paragraph}>
            When you use our video identification service, we collect and process the video content you submit for identification. This may include visual data, audio data, and metadata from the video clips.
          </Text>
          
          <Text style={styles.subheading}>1.3 Derivative Data</Text>
          <Text style={styles.paragraph}>
            Information our servers automatically collect when you access the Service, such as your IP address, browser type, operating system, access times, and the pages you have viewed directly before and after accessing the Service.
          </Text>
          
          <Text style={styles.subheading}>1.4 Mobile Device Data</Text>
          <Text style={styles.paragraph}>
            Device information such as your mobile device ID number, model, and manufacturer, version of your operating system, phone number, country, location, and any other data you choose to provide.
          </Text>
          
          <Text style={styles.subheading}>1.5 Usage Data</Text>
          <Text style={styles.paragraph}>
            Information about how you interact with our Service, including search queries, features used, identification history, and user preferences.
          </Text>
          
          <Text style={styles.sectionTitle}>2. USE OF YOUR INFORMATION</Text>
          <Text style={styles.paragraph}>
            Having accurate information about you permits us to provide you with a smooth, efficient, and customized experience. Specifically, we may use information collected about you via the Service to:
          </Text>
          <Text style={styles.bulletPoint}>u2022 Create and manage your account</Text>
          <Text style={styles.bulletPoint}>u2022 Process video identification requests</Text>
          <Text style={styles.bulletPoint}>u2022 Compile anonymous statistical data and analysis for internal use or with third parties</Text>
          <Text style={styles.bulletPoint}>u2022 Deliver targeted advertising, newsletters, and other information regarding promotions and the Service to you</Text>
          <Text style={styles.bulletPoint}>u2022 Email you regarding your account or order</Text>
          <Text style={styles.bulletPoint}>u2022 Enable user-to-user communications</Text>
          <Text style={styles.bulletPoint}>u2022 Generate a personal profile about you to make future visits to the Service more personalized</Text>
          <Text style={styles.bulletPoint}>u2022 Increase the efficiency and operation of the Service</Text>
          <Text style={styles.bulletPoint}>u2022 Monitor and analyze usage and trends to improve your experience with the Service</Text>
          <Text style={styles.bulletPoint}>u2022 Notify you of updates to the Service</Text>
          <Text style={styles.bulletPoint}>u2022 Request feedback and contact you about your use of the Service</Text>
          <Text style={styles.bulletPoint}>u2022 Resolve disputes and troubleshoot problems</Text>
          <Text style={styles.bulletPoint}>u2022 Respond to product and customer service requests</Text>
          
          <Text style={styles.sectionTitle}>3. DISCLOSURE OF YOUR INFORMATION</Text>
          <Text style={styles.paragraph}>
            We may share information we have collected about you in certain situations. Your information may be disclosed as follows:
          </Text>
          
          <Text style={styles.subheading}>3.1 By Law or to Protect Rights</Text>
          <Text style={styles.paragraph}>
            If we believe the release of information about you is necessary to respond to legal process, to investigate or remedy potential violations of our policies, or to protect the rights, property, and safety of others, we may share your information as permitted or required by any applicable law, rule, or regulation.
          </Text>
          
          <Text style={styles.subheading}>3.2 Third-Party Service Providers</Text>
          <Text style={styles.paragraph}>
            We may share your information with third parties that perform services for us or on our behalf, including payment processing, data analysis, email delivery, hosting services, customer service, and marketing assistance.
          </Text>
          
          <Text style={styles.subheading}>3.3 Marketing Communications</Text>
          <Text style={styles.paragraph}>
            With your consent, or with an opportunity for you to withdraw consent, we may share your information with third parties for marketing purposes, as permitted by law.
          </Text>
          
          <Text style={styles.subheading}>3.4 Interactions with Other Users</Text>
          <Text style={styles.paragraph}>
            If you interact with other users of the Service, those users may see your name, profile photo, and descriptions of your activity.
          </Text>
          
          <Text style={styles.subheading}>3.5 Business Transfers</Text>
          <Text style={styles.paragraph}>
            If we are involved in a merger, acquisition, or sale of all or a portion of our assets, your information may be transferred as part of that transaction. We will notify you via email and/or a prominent notice on our Service of any change in ownership or uses of your information, as well as any choices you may have regarding your information.
          </Text>
          
          <Text style={styles.sectionTitle}>4. SECURITY OF YOUR INFORMATION</Text>
          <Text style={styles.paragraph}>
            We use administrative, technical, and physical security measures to help protect your personal information. While we have taken reasonable steps to secure the personal information you provide to us, please be aware that despite our efforts, no security measures are perfect or impenetrable, and no method of data transmission can be guaranteed against any interception or other type of misuse.
          </Text>
          
          <Text style={styles.sectionTitle}>5. POLICY FOR CHILDREN</Text>
          <Text style={styles.paragraph}>
            We do not knowingly solicit information from or market to children under the age of 13. If you become aware of any data we have collected from children under age 13, please contact us using the contact information provided below.
          </Text>
          
          <Text style={styles.sectionTitle}>6. OPTIONS REGARDING YOUR INFORMATION</Text>
          
          <Text style={styles.subheading}>6.1 Account Information</Text>
          <Text style={styles.paragraph}>
            You may at any time review or change the information in your account or terminate your account by:
          </Text>
          <Text style={styles.bulletPoint}>u2022 Logging into your account settings and updating your account</Text>
          <Text style={styles.bulletPoint}>u2022 Contacting us using the contact information provided below</Text>
          <Text style={styles.paragraph}>
            Upon your request to terminate your account, we will deactivate or delete your account and information from our active databases. However, some information may be retained in our files to prevent fraud, troubleshoot problems, assist with any investigations, enforce our Terms of Use and/or comply with legal requirements.
          </Text>
          
          <Text style={styles.subheading}>6.2 Emails and Communications</Text>
          <Text style={styles.paragraph}>
            If you no longer wish to receive correspondence, emails, or other communications from us, you may opt-out by:
          </Text>
          <Text style={styles.bulletPoint}>u2022 Noting your preferences at the time you register your account with the Service</Text>
          <Text style={styles.bulletPoint}>u2022 Logging into your account settings and updating your preferences</Text>
          <Text style={styles.bulletPoint}>u2022 Contacting us using the contact information provided below</Text>
          
          <Text style={styles.sectionTitle}>7. CALIFORNIA PRIVACY RIGHTS</Text>
          <Text style={styles.paragraph}>
            California Civil Code Section 1798.83, also known as the "Shine The Light" law, permits our users who are California residents to request and obtain from us, once a year and free of charge, information about categories of personal information (if any) we disclosed to third parties for direct marketing purposes and the names and addresses of all third parties with which we shared personal information in the immediately preceding calendar year. If you are a California resident and would like to make such a request, please submit your request in writing to us using the contact information provided below.
          </Text>
          
          <Text style={styles.sectionTitle}>8. CONTACT US</Text>
          <Text style={styles.paragraph}>
            If you have questions or comments about this Privacy Policy, please contact us at:
          </Text>
          <Text style={styles.contactInfo}>
            VidID Technologies, Inc.
          </Text>
          <Text style={styles.contactInfo}>
            123 Innovation Way
          </Text>
          <Text style={styles.contactInfo}>
            Silicon Valley, CA 94043
          </Text>
          <Text style={styles.contactInfo}>
            Email: privacy@vidid.com
          </Text>
          <Text style={styles.contactInfo}>
            Phone: (800) 555-1234
          </Text>
          
          <View style={styles.footer}>
            <Text style={styles.footerText}>u00a9 2025 VidID Technologies, Inc. All rights reserved.</Text>
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f9f9f9',
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
  contentContainer: {
    padding: 20,
    paddingBottom: 40,
  },
  lastUpdated: {
    fontSize: 14,
    color: '#888',
    marginBottom: 20,
    fontStyle: 'italic',
  },
  introduction: {
    fontSize: 15,
    lineHeight: 24,
    color: '#444',
    marginBottom: 15,
  },
  sectionTitle: {
    fontSize: 17,
    fontWeight: 'bold',
    color: '#333',
    marginTop: 25,
    marginBottom: 15,
  },
  subheading: {
    fontSize: 16,
    fontWeight: '600',
    color: '#444',
    marginTop: 15,
    marginBottom: 10,
  },
  paragraph: {
    fontSize: 15,
    lineHeight: 24,
    color: '#444',
    marginBottom: 15,
  },
  bulletPoint: {
    fontSize: 15,
    lineHeight: 24,
    color: '#444',
    marginBottom: 8,
    marginLeft: 15,
  },
  contactInfo: {
    fontSize: 15,
    lineHeight: 22,
    color: '#444',
    marginBottom: 5,
  },
  footer: {
    marginTop: 30,
    paddingTop: 20,
    borderTopWidth: 1,
    borderTopColor: '#eee',
    alignItems: 'center',
  },
  footerText: {
    fontSize: 14,
    color: '#888',
  },
});

export default PrivacyPolicyScreen;
