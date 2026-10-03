/**
 * Modern Button Components
 * Buttons with animations
 */

'use client';

import React, { ReactNode } from 'react';
import { motion } from 'framer-motion';
import { Loader2, Plus } from 'lucide-react';
import { cn } from '@/lib/utils';

// ============================================
// BUTTON VARIANTS
// ============================================
type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'ghost' | 'gradient' | 'glow';
type ButtonSize = 'sm' | 'md' | 'lg' | 'xl';

interface ButtonProps {
  children: ReactNode;
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  disabled?: boolean;
  icon?: ReactNode;
  iconPosition?: 'left' | 'right';
  onClick?: () => void;
  className?: string;
  fullWidth?: boolean;
}

const buttonVariants: Record<ButtonVariant, string> = {
  primary: 'bg-indigo-600 text-white hover:bg-indigo-700 shadow-lg shadow-indigo-500/30',
  secondary: 'bg-gray-200 dark:bg-gray-800 text-gray-900 dark:text-white hover:bg-gray-300 dark:hover:bg-gray-700',
  outline: 'border-2 border-indigo-600 text-indigo-600 hover:bg-indigo-50 dark:hover:bg-indigo-950',
  ghost: 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800',
  gradient: 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white hover:from-indigo-700 hover:to-purple-700 shadow-lg shadow-indigo-500/30',
  glow: 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-[0_0_30px_rgba(99,102,241,0.5)] hover:shadow-[0_0_50px_rgba(99,102,241,0.7)]'
};

const buttonSizes: Record<ButtonSize, string> = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-4 py-2 text-base',
  lg: 'px-6 py-3 text-lg',
  xl: 'px-8 py-4 text-xl'
};

export function ModernButton({
  children,
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled = false,
  icon,
  iconPosition = 'right',
  onClick,
  className,
  fullWidth = false
}: ButtonProps) {
  const isDisabled = disabled || loading;

  return (
    <motion.button
      whileHover={!isDisabled ? { scale: 1.05, y: -2 } : undefined}
      whileTap={!isDisabled ? { scale: 0.95 } : undefined}
      onClick={!isDisabled ? onClick : undefined}
      className={cn(
        'inline-flex items-center justify-center gap-2 rounded-xl font-semibold transition-all',
        buttonVariants[variant],
        buttonSizes[size],
        fullWidth && 'w-full',
        isDisabled && 'opacity-50 cursor-not-allowed',
        className
      )}
      disabled={isDisabled}
    >
      {loading && <Loader2 className="w-4 h-4 animate-spin" />}
      {!loading && icon && iconPosition === 'left' && icon}
      {children}
      {!loading && icon && iconPosition === 'right' && icon}
    </motion.button>
  );
}

// ============================================
// MAGNETIC BUTTON
// ============================================
export function MagneticButton({
  children,
  className,
  onClick
}: {
  children: ReactNode;
  className?: string;
  onClick?: () => void;
}) {
  const [position, setPosition] = React.useState({ x: 0, y: 0 });

  const handleMouseMove = (e: React.MouseEvent<HTMLButtonElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left - rect.width / 2;
    const y = e.clientY - rect.top - rect.height / 2;
    setPosition({ x: x * 0.3, y: y * 0.3 });
  };

  const handleMouseLeave = () => {
    setPosition({ x: 0, y: 0 });
  };

  return (
    <motion.button
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      onClick={onClick}
      animate={{ x: position.x, y: position.y }}
      transition={{ type: 'spring', stiffness: 300, damping: 20 }}
      className={cn(
        'px-6 py-3 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-semibold shadow-lg',
        className
      )}
    >
      {children}
    </motion.button>
  );
}

// ============================================
// SHIMMER BUTTON
// ============================================
export function ShimmerButton({
  children,
  className,
  onClick
}: {
  children: ReactNode;
  className?: string;
  onClick?: () => void;
}) {
  return (
    <motion.button
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      onClick={onClick}
      className={cn(
        'relative overflow-hidden px-6 py-3 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-semibold',
        className
      )}
    >
      <span className="relative z-10">{children}</span>
      <motion.div
        className="absolute inset-0 bg-gradient-to-r from-transparent via-white to-transparent opacity-30"
        initial={{ x: '-100%' }}
        whileHover={{ x: '100%' }}
        transition={{ duration: 0.6 }}
      />
    </motion.button>
  );
}

// ============================================
// RIPPLE BUTTON
// ============================================
export function RippleButton({
  children,
  className,
  onClick
}: {
  children: ReactNode;
  className?: string;
  onClick?: () => void;
}) {
  const [ripples, setRipples] = React.useState<{ x: number; y: number; id: number }[]>([]);

  const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    const newRipple = { x, y, id: Date.now() };
    setRipples([...ripples, newRipple]);
    
    setTimeout(() => {
      setRipples(ripples.filter(r => r.id !== newRipple.id));
    }, 600);

    onClick?.();
  };

  return (
    <motion.button
      onClick={handleClick}
      className={cn(
        'relative overflow-hidden px-6 py-3 rounded-xl bg-indigo-600 text-white font-semibold',
        className
      )}
    >
      {children}
      {ripples.map((ripple) => (
        <motion.span
          key={ripple.id}
          className="absolute rounded-full bg-white pointer-events-none"
          style={{
            left: ripple.x,
            top: ripple.y,
            width: 0,
            height: 0,
          }}
          initial={{ width: 0, height: 0, opacity: 0.5 }}
          animate={{ width: 100, height: 100, opacity: 0 }}
          transition={{ duration: 0.6 }}
        />
      ))}
    </motion.button>
  );
}

// ============================================
// ICON BUTTONS
// ============================================
export function IconButton({
  icon,
  size = 'md',
  variant = 'ghost',
  onClick,
  className
}: {
  icon: ReactNode;
  size?: ButtonSize;
  variant?: ButtonVariant;
  onClick?: () => void;
  className?: string;
}) {
  return (
    <motion.button
      whileHover={{ scale: 1.1, rotate: 5 }}
      whileTap={{ scale: 0.9 }}
      onClick={onClick}
      className={cn(
        'inline-flex items-center justify-center rounded-lg transition-all',
        buttonVariants[variant],
        size === 'sm' && 'p-1.5',
        size === 'md' && 'p-2',
        size === 'lg' && 'p-3',
        size === 'xl' && 'p-4',
        className
      )}
    >
      {icon}
    </motion.button>
  );
}

// ============================================
// FLOATING ACTION BUTTON
// ============================================
export function FAB({
  icon = <Plus className="w-6 h-6" />,
  onClick,
  className
}: {
  icon?: ReactNode;
  onClick?: () => void;
  className?: string;
}) {
  return (
    <motion.button
      whileHover={{ scale: 1.1, rotate: 90 }}
      whileTap={{ scale: 0.9 }}
      onClick={onClick}
      className={cn(
        'fixed bottom-8 right-8 z-50 w-16 h-16 rounded-full bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-2xl shadow-indigo-500/50 flex items-center justify-center',
        className
      )}
      initial={{ scale: 0 }}
      animate={{ scale: 1 }}
      transition={{ type: 'spring', stiffness: 300, damping: 20 }}
    >
      {icon}
    </motion.button>
  );
}

// ============================================
// BUTTON GROUP
// ============================================
export function ButtonGroup({
  children,
  className
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn('inline-flex gap-2', className)}>
      {children}
    </div>
  );
}

// ============================================
// SPLIT BUTTON
// ============================================
export function SplitButton({
  mainLabel,
  mainOnClick,
  options
}: {
  mainLabel: string;
  mainOnClick: () => void;
  options: { label: string; onClick: () => void }[];
}) {
  const [isOpen, setIsOpen] = React.useState(false);

  return (
    <div className="relative inline-flex">
      <motion.button
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        onClick={mainOnClick}
        className="px-6 py-3 rounded-l-xl bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-semibold"
      >
        {mainLabel}
      </motion.button>
      
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={() => setIsOpen(!isOpen)}
        className="px-3 py-3 rounded-r-xl bg-purple-700 text-white border-l border-purple-800"
      >
        <motion.div
          animate={{ rotate: isOpen ? 180 : 0 }}
          transition={{ duration: 0.3 }}
        >
          ▼
        </motion.div>
      </motion.button>

      {isOpen && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          className="absolute top-full mt-2 right-0 bg-white dark:bg-gray-800 rounded-xl shadow-xl border border-gray-200 dark:border-gray-700 overflow-hidden min-w-[200px] z-50"
        >
          {options.map((option, index) => (
            <motion.button
              key={index}
              whileHover={{ backgroundColor: 'rgba(99, 102, 241, 0.1)' }}
              onClick={() => {
                option.onClick();
                setIsOpen(false);
              }}
              className="w-full px-4 py-2 text-left text-gray-700 dark:text-gray-300 hover:text-indigo-600 transition-colors"
            >
              {option.label}
            </motion.button>
          ))}
        </motion.div>
      )}
    </div>
  );
}

// ============================================
// PRESET BUTTONS
// ============================================
export const PrimaryButton = (props: Omit<ButtonProps, 'variant'>) => (
  <ModernButton variant="primary" {...props} />
);

export const SecondaryButton = (props: Omit<ButtonProps, 'variant'>) => (
  <ModernButton variant="secondary" {...props} />
);

export const GradientButton = (props: Omit<ButtonProps, 'variant'>) => (
  <ModernButton variant="gradient" {...props} />
);

export const GlowButton = (props: Omit<ButtonProps, 'variant'>) => (
  <ModernButton variant="glow" {...props} />
);
