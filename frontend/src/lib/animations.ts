/**
 * Advanced Animation Utilities & Variants
 * Animation configurations
 */

import { Variants } from 'framer-motion';

// ============================================
// FADE ANIMATIONS
// ============================================
export const fadeIn: Variants = {
  hidden: { opacity: 0 },
  visible: { 
    opacity: 1,
    transition: { duration: 0.6, ease: [0.25, 0.1, 0.25, 1] }
  }
};

export const fadeInUp: Variants = {
  hidden: { opacity: 0, y: 40 },
  visible: { 
    opacity: 1, 
    y: 0,
    transition: { duration: 0.7, ease: [0.25, 0.1, 0.25, 1] }
  }
};

export const fadeInDown: Variants = {
  hidden: { opacity: 0, y: -40 },
  visible: { 
    opacity: 1, 
    y: 0,
    transition: { duration: 0.7, ease: [0.25, 0.1, 0.25, 1] }
  }
};

export const fadeInLeft: Variants = {
  hidden: { opacity: 0, x: -60 },
  visible: { 
    opacity: 1, 
    x: 0,
    transition: { duration: 0.7, ease: [0.25, 0.1, 0.25, 1] }
  }
};

export const fadeInRight: Variants = {
  hidden: { opacity: 0, x: 60 },
  visible: { 
    opacity: 1, 
    x: 0,
    transition: { duration: 0.7, ease: [0.25, 0.1, 0.25, 1] }
  }
};

// ============================================
// SCALE ANIMATIONS
// ============================================
export const scaleIn: Variants = {
  hidden: { opacity: 0, scale: 0.8 },
  visible: { 
    opacity: 1, 
    scale: 1,
    transition: { duration: 0.5, ease: [0.34, 1.56, 0.64, 1] }
  }
};

export const scaleOut: Variants = {
  visible: { opacity: 1, scale: 1 },
  hidden: { 
    opacity: 0, 
    scale: 0.8,
    transition: { duration: 0.3 }
  }
};

// ============================================
// STAGGER ANIMATIONS
// ============================================
export const staggerContainer: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.2
    }
  }
};

export const staggerItem: Variants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.5 }
  }
};

// ============================================
// 3D & ROTATE ANIMATIONS
// ============================================
export const rotateIn: Variants = {
  hidden: { opacity: 0, rotate: -180, scale: 0.5 },
  visible: {
    opacity: 1,
    rotate: 0,
    scale: 1,
    transition: { duration: 0.8, ease: [0.34, 1.56, 0.64, 1] }
  }
};

export const flipCard: Variants = {
  initial: { rotateY: 0 },
  flipped: { 
    rotateY: 180,
    transition: { duration: 0.6, ease: [0.34, 1.56, 0.64, 1] }
  }
};

export const tiltIn: Variants = {
  hidden: { 
    opacity: 0, 
    rotateX: 90,
    transformPerspective: 1000
  },
  visible: {
    opacity: 1,
    rotateX: 0,
    transition: { duration: 0.8, ease: [0.34, 1.56, 0.64, 1] }
  }
};

// ============================================
// SLIDE ANIMATIONS
// ============================================
export const slideInFromBottom: Variants = {
  hidden: { y: '100%', opacity: 0 },
  visible: {
    y: 0,
    opacity: 1,
    transition: { duration: 0.6, ease: [0.25, 0.1, 0.25, 1] }
  }
};

export const slideInFromTop: Variants = {
  hidden: { y: '-100%', opacity: 0 },
  visible: {
    y: 0,
    opacity: 1,
    transition: { duration: 0.6, ease: [0.25, 0.1, 0.25, 1] }
  }
};

// ============================================
// HOVER ANIMATIONS
// ============================================
export const hoverScale = {
  scale: 1.05,
  transition: { duration: 0.3, ease: [0.34, 1.56, 0.64, 1] }
};

export const hoverLift = {
  y: -8,
  scale: 1.02,
  boxShadow: '0 20px 40px rgba(0, 0, 0, 0.15)',
  transition: { duration: 0.3 }
};

export const hoverGlow = {
  boxShadow: '0 0 30px rgba(99, 102, 241, 0.5)',
  transition: { duration: 0.3 }
};

// ============================================
// CARD ANIMATIONS
// ============================================
export const cardHover: Variants = {
  rest: {
    scale: 1,
    y: 0,
    boxShadow: '0 10px 30px -15px rgba(0, 0, 0, 0.2)'
  },
  hover: {
    scale: 1.03,
    y: -8,
    boxShadow: '0 20px 40px -15px rgba(0, 0, 0, 0.3)',
    transition: {
      duration: 0.3,
      ease: [0.34, 1.56, 0.64, 1]
    }
  }
};

export const glassCard: Variants = {
  hidden: { 
    opacity: 0, 
    y: 40,
    backdropFilter: 'blur(0px)'
  },
  visible: {
    opacity: 1,
    y: 0,
    backdropFilter: 'blur(20px)',
    transition: { duration: 0.7 }
  }
};

// ============================================
// TEXT ANIMATIONS
// ============================================
export const letterAnimation: Variants = {
  hidden: { 
    opacity: 0, 
    y: 50 
  },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.5
    }
  }
};

export const wordAnimation: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.08
    }
  }
};

// ============================================
// LOADING ANIMATIONS
// ============================================
export const pulseAnimation: Variants = {
  initial: { scale: 1, opacity: 1 },
  animate: {
    scale: [1, 1.2, 1],
    opacity: [1, 0.8, 1],
    transition: {
      duration: 2,
      repeat: Infinity,
      ease: 'easeInOut'
    }
  }
};

export const spinAnimation: Variants = {
  animate: {
    rotate: 360,
    transition: {
      duration: 1,
      repeat: Infinity,
      ease: 'linear'
    }
  }
};

export const bounceAnimation: Variants = {
  animate: {
    y: [-10, 10, -10],
    transition: {
      duration: 1.5,
      repeat: Infinity,
      ease: 'easeInOut'
    }
  }
};

// ============================================
// PAGE TRANSITION ANIMATIONS
// ============================================
export const pageTransition: Variants = {
  initial: { opacity: 0, x: -200, scale: 0.95 },
  animate: { 
    opacity: 1, 
    x: 0, 
    scale: 1,
    transition: { 
      duration: 0.6,
      ease: [0.25, 0.1, 0.25, 1]
    }
  },
  exit: { 
    opacity: 0, 
    x: 200, 
    scale: 0.95,
    transition: { 
      duration: 0.4 
    }
  }
};

// ============================================
// SCROLL REVEAL ANIMATIONS
// ============================================
export const scrollReveal: Variants = {
  hidden: { 
    opacity: 0, 
    y: 75,
    scale: 0.9
  },
  visible: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: {
      duration: 0.8,
      ease: [0.25, 0.1, 0.25, 1]
    }
  }
};

// ============================================
// HERO ANIMATIONS
// ============================================
export const heroAnimation: Variants = {
  hidden: { 
    opacity: 0,
    scale: 0.8,
    y: 60
  },
  visible: {
    opacity: 1,
    scale: 1,
    y: 0,
    transition: {
      duration: 1,
      ease: [0.25, 0.1, 0.25, 1],
      staggerChildren: 0.2
    }
  }
};

// ============================================
// NAVBAR ANIMATIONS
// ============================================
export const navbarAnimation: Variants = {
  hidden: { 
    y: -100, 
    opacity: 0 
  },
  visible: {
    y: 0,
    opacity: 1,
    transition: {
      duration: 0.6,
      ease: [0.25, 0.1, 0.25, 1]
    }
  }
};

export const navItemAnimation: Variants = {
  hidden: { opacity: 0, y: -20 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: {
      delay: i * 0.1,
      duration: 0.5
    }
  })
};

// ============================================
// MODAL ANIMATIONS
// ============================================
export const modalBackdrop: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { duration: 0.3 }
  }
};

export const modalContent: Variants = {
  hidden: { 
    opacity: 0, 
    scale: 0.8,
    y: 50
  },
  visible: {
    opacity: 1,
    scale: 1,
    y: 0,
    transition: {
      duration: 0.4,
      ease: [0.34, 1.56, 0.64, 1]
    }
  }
};

// ============================================
// NOTIFICATION ANIMATIONS
// ============================================
export const notificationSlide: Variants = {
  hidden: { 
    x: 400, 
    opacity: 0,
    scale: 0.8
  },
  visible: {
    x: 0,
    opacity: 1,
    scale: 1,
    transition: {
      duration: 0.5,
      ease: [0.34, 1.56, 0.64, 1]
    }
  },
  exit: {
    x: 400,
    opacity: 0,
    scale: 0.8,
    transition: { duration: 0.3 }
  }
};

// ============================================
// UTILITY FUNCTIONS
// ============================================

/**
 * Create stagger animation with custom delay
 */
export const createStagger = (staggerDelay: number = 0.1) => ({
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: staggerDelay
    }
  }
});

/**
 * Create custom transition
 */
export const customTransition = (duration: number = 0.5, ease: string | number[] = 'easeInOut') => ({
  duration,
  ease
});

/**
 * Spring configuration presets
 */
export const springConfigs = {
  gentle: { stiffness: 100, damping: 15 },
  wobbly: { stiffness: 180, damping: 12 },
  stiff: { stiffness: 400, damping: 30 },
  slow: { stiffness: 50, damping: 20 },
  bouncy: { stiffness: 300, damping: 10 }
};
