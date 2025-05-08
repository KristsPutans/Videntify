/**
 * VidID Logo Component
 * Vector-based logo that can be used throughout the app
 */

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Svg, Path, Circle } from 'react-native-svg';
import { colors } from '../utils/theme';

const VidIDLogo = ({ size = 60, color = colors.primary }) => {
  // Calculate dimensions based on size
  const viewBoxSize = 100;
  const scale = size / viewBoxSize;
  const fontSize = Math.floor(size * 0.45);
  
  return (
    <View style={[styles.container, { width: size, height: size }]}>
      <Svg width={size} height={size} viewBox={`0 0 ${viewBoxSize} ${viewBoxSize}`}>
        {/* Camera Body */}
        <Path
          d={`M20 30 L70 30 L70 70 L20 70 Z`}
          fill={color}
          strokeWidth="2"
        />
        
        {/* Camera Lens */}
        <Circle
          cx="45"
          cy="50"
          r="15"
          fill="#fff"
          stroke={color}
          strokeWidth="2"
        />
        
        {/* Inner Lens */}
        <Circle
          cx="45"
          cy="50"
          r="8"
          fill={color}
        />
        
        {/* Camera Flash */}
        <Circle
          cx="60"
          cy="40"
          r="5"
          fill="#fff"
        />
        
        {/* Film Strip */}
        <Path
          d={`M75 35 L90 30 L90 70 L75 65 Z`}
          fill={color}
          strokeWidth="2"
        />
        
        {/* Film Holes */}
        <Circle cx="82" cy="40" r="2" fill="#fff" />
        <Circle cx="82" cy="50" r="2" fill="#fff" />
        <Circle cx="82" cy="60" r="2" fill="#fff" />
      </Svg>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
  },
});

export default VidIDLogo;
