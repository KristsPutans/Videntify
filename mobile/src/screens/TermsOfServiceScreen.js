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

const TermsOfServiceScreen = () => {
  const navigation = useNavigation();

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
          <Ionicons name="arrow-back" size={24} color="#333" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Terms of Service</Text>
        <View style={styles.backButtonPlaceholder} />
      </View>

      <ScrollView style={styles.scrollView}>
        <View style={styles.contentContainer}>
          <Text style={styles.lastUpdated}>Last Updated: May 1, 2025</Text>
          
          <Text style={styles.sectionTitle}>1. Acceptance of Terms</Text>
          <Text style={styles.paragraph}>
            By accessing or using the VidID application ("App"), you agree to be bound by these Terms of Service ("Terms"), whether you are a registered user or not. These Terms govern your use of the App and any services, features, content, or applications operated by VidID Technologies, Inc. ("we," "us," or "our").
          </Text>
          <Text style={styles.paragraph}>
            If you do not agree to these Terms, you may not access or use the App. We may update these Terms from time to time, and your continued use of the App following any changes constitutes your acceptance of the revised Terms.
          </Text>
          
          <Text style={styles.sectionTitle}>2. Account Registration</Text>
          <Text style={styles.paragraph}>
            To use certain features of the App, you may need to register for an account. You agree to provide accurate, current, and complete information during the registration process and to update such information to keep it accurate, current, and complete.
          </Text>
          <Text style={styles.paragraph}>
            You are responsible for safeguarding your password and for all activities that occur under your account. You agree to notify us immediately of any unauthorized use of your account or any other breach of security.
          </Text>
          
          <Text style={styles.sectionTitle}>3. User Content</Text>
          <Text style={styles.paragraph}>
            You retain all rights in any content you submit, post, or display on or through the App ("User Content"). By submitting User Content to the App, you grant us a worldwide, non-exclusive, royalty-free license to use, reproduce, modify, adapt, publish, translate, distribute, and display such User Content for the purpose of providing and improving the App.
          </Text>
          <Text style={styles.paragraph}>
            You represent and warrant that: (i) you own the User Content or have the right to use and grant us the rights and license as provided in these Terms, and (ii) the posting of your User Content does not violate the privacy rights, publicity rights, copyrights, contract rights, or any other rights of any person or entity.
          </Text>
          
          <Text style={styles.sectionTitle}>4. Prohibited Conduct</Text>
          <Text style={styles.paragraph}>
            You agree not to engage in any of the following prohibited activities:
          </Text>
          <Text style={styles.bulletPoint}>• Using the App for any illegal purpose or in violation of any laws</Text>
          <Text style={styles.bulletPoint}>• Attempting to interfere with, compromise the system integrity or security, or decipher any transmissions to or from the servers running the App</Text>
          <Text style={styles.bulletPoint}>• Uploading invalid data, viruses, worms, or other software agents through the App</Text>
          <Text style={styles.bulletPoint}>• Collecting or harvesting any personally identifiable information from the App</Text>
          <Text style={styles.bulletPoint}>• Impersonating another person or otherwise misrepresenting your affiliation with a person or entity</Text>
          <Text style={styles.bulletPoint}>• Using the App to send unsolicited communications or promotions</Text>
          
          <Text style={styles.sectionTitle}>5. Intellectual Property Rights</Text>
          <Text style={styles.paragraph}>
            The App and its original content, features, and functionality are and will remain the exclusive property of VidID Technologies, Inc. and its licensors. The App is protected by copyright, trademark, and other laws of both the United States and foreign countries.
          </Text>
          <Text style={styles.paragraph}>
            Our trademarks and trade dress may not be used in connection with any product or service without the prior written consent of VidID Technologies, Inc.
          </Text>
          
          <Text style={styles.sectionTitle}>6. Privacy Policy</Text>
          <Text style={styles.paragraph}>
            Please refer to our Privacy Policy for information about how we collect, use, and disclose information about you.
          </Text>
          
          <Text style={styles.sectionTitle}>7. Termination</Text>
          <Text style={styles.paragraph}>
            We may terminate or suspend your account and access to the App immediately, without prior notice or liability, for any reason, including if you breach the Terms. Upon termination, your right to use the App will immediately cease.
          </Text>
          
          <Text style={styles.sectionTitle}>8. Disclaimer of Warranties</Text>
          <Text style={styles.paragraph}>
            THE APP IS PROVIDED ON AN "AS IS" AND "AS AVAILABLE" BASIS. VidID TECHNOLOGIES, INC. EXPRESSLY DISCLAIMS ALL WARRANTIES OF ANY KIND, WHETHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND NON-INFRINGEMENT.
          </Text>
          <Text style={styles.paragraph}>
            WE MAKE NO WARRANTY THAT (I) THE APP WILL MEET YOUR REQUIREMENTS, (II) THE APP WILL BE UNINTERRUPTED, TIMELY, SECURE, OR ERROR-FREE, (III) THE RESULTS THAT MAY BE OBTAINED FROM THE USE OF THE APP WILL BE ACCURATE OR RELIABLE, OR (IV) THE QUALITY OF ANY PRODUCTS, SERVICES, INFORMATION, OR OTHER MATERIAL OBTAINED THROUGH THE APP WILL MEET YOUR EXPECTATIONS.
          </Text>
          
          <Text style={styles.sectionTitle}>9. Limitation of Liability</Text>
          <Text style={styles.paragraph}>
            IN NO EVENT SHALL VidID TECHNOLOGIES, INC., ITS DIRECTORS, EMPLOYEES, PARTNERS, AGENTS, SUPPLIERS, OR AFFILIATES, BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES, INCLUDING WITHOUT LIMITATION, LOSS OF PROFITS, DATA, USE, GOODWILL, OR OTHER INTANGIBLE LOSSES, RESULTING FROM (I) YOUR ACCESS TO OR USE OF OR INABILITY TO ACCESS OR USE THE APP; (II) ANY CONDUCT OR CONTENT OF ANY THIRD PARTY ON THE APP; (III) ANY CONTENT OBTAINED FROM THE APP; AND (IV) UNAUTHORIZED ACCESS, USE, OR ALTERATION OF YOUR TRANSMISSIONS OR CONTENT.
          </Text>
          
          <Text style={styles.sectionTitle}>10. Governing Law</Text>
          <Text style={styles.paragraph}>
            These Terms shall be governed and construed in accordance with the laws of the State of California, United States, without regard to its conflict of law provisions. Our failure to enforce any right or provision of these Terms will not be considered a waiver of those rights.
          </Text>
          
          <Text style={styles.sectionTitle}>11. Changes to Terms</Text>
          <Text style={styles.paragraph}>
            We reserve the right, at our sole discretion, to modify or replace these Terms at any time. We will provide notice of any changes by posting the new Terms on the App. Your continued use of the App after any such changes constitutes your acceptance of the new Terms.
          </Text>
          
          <Text style={styles.sectionTitle}>12. Contact Us</Text>
          <Text style={styles.paragraph}>
            If you have any questions about these Terms, please contact us at legal@vidid.com.
          </Text>
          
          <View style={styles.footer}>
            <Text style={styles.footerText}>© 2025 VidID Technologies, Inc. All rights reserved.</Text>
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
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginTop: 25,
    marginBottom: 15,
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
    marginBottom: 10,
    marginLeft: 15,
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

export default TermsOfServiceScreen;
