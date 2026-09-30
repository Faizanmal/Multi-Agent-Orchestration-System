"use client";

import React, { useState } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { FaGithub } from 'react-icons/fa';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import {
  Eye,
  EyeOff,
  Mail,
  Lock,
  Sparkles,
  ArrowRight,
  Globe,
  Loader2,
  User,
  Building2,
  Check,
  AlertCircle,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { cn } from '@/lib/utils';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';

const registerSchema = z.object({
  firstName: z.string().min(2, 'First name must be at least 2 characters'),
  lastName: z.string().min(2, 'Last name must be at least 2 characters'),
  email: z.string().email('Please enter a valid email address'),
  company: z.string().optional(),
  plan: z.enum(['free', 'pro', 'enterprise']),
  password: z.string()
    .min(8, 'Password must be at least 8 characters')
    .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
    .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
    .regex(/[0-9]/, 'Password must contain at least one number'),
  confirmPassword: z.string(),
  acceptTerms: z.boolean().refine(val => val === true, {
    message: 'You must accept the terms and conditions',
  }),
}).refine(data => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ['confirmPassword'],
});

type RegisterFormValues = z.infer<typeof registerSchema>;

const plans = [
  {
    id: 'free',
    name: 'Free',
    price: '$0',
    description: 'For individuals and small projects',
    features: ['Up to 3 Agents', '100 messages/month', 'Community support'],
  },
  {
    id: 'pro',
    name: 'Pro',
    price: '$49',
    description: 'For growing teams and businesses',
    features: ['Unlimited Agents', '10,000 messages/month', 'Priority support', 'Advanced analytics'],
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    price: 'Custom',
    description: 'For large organizations',
    features: ['1,000,000 messages/month', 'Dedicated support', 'SSO & audit logs', 'Custom limits'],
  },
];

export default function RegisterPage() {
  const router = useRouter();
  const { register, loginWithGoogle, loginWithGitHub } = useAuth();
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [oauthLoading, setOauthLoading] = useState<'google' | 'github' | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [step, setStep] = useState(1);

  const form = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      firstName: '',
      lastName: '',
      email: '',
      company: '',
      plan: 'free',
      password: '',
      confirmPassword: '',
      acceptTerms: false,
    },
  });

  const onSubmit = async (data: RegisterFormValues) => {
    setError(null);
    setIsLoading(true);
    try {
      await register({
        email: data.email,
        password: data.password,
        first_name: data.firstName,
        last_name: data.lastName,
        username: data.email.split('@')[0],
      });
      router.push('/dashboard');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Registration failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const getPasswordStrength = (password: string) => {
    let strength = 0;
    if (password.length >= 8) strength++;
    if (/[A-Z]/.test(password)) strength++;
    if (/[a-z]/.test(password)) strength++;
    if (/[0-9]/.test(password)) strength++;
    if (/[^A-Za-z0-9]/.test(password)) strength++;
    return strength;
  };

  // eslint-disable-next-line react-hooks/incompatible-library
  const password = form.watch('password');
  const passwordStrength = getPasswordStrength(password);

  return (
    <div className="min-h-screen flex">
      {/* Left Panel - Form */}
      <div className="flex-1 flex items-center justify-center p-8 bg-background overflow-y-auto">
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5 }}
          className="w-full max-w-lg"
        >
          {/* Logo */}
          <div className="flex items-center gap-3 mb-8">
            <div className="relative h-10 w-10 flex items-center justify-center">
              <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-500" />
              <Sparkles className="relative h-5 w-5 text-white" />
            </div>
            <span className="text-2xl font-bold gradient-text">MultiAgent AI</span>
          </div>

          {/* Header */}
          <div className="mb-8">
            <h2 className="text-3xl font-bold mb-2">Create your account</h2>
            <p className="text-muted-foreground">
              Start your journey with intelligent AI agents
            </p>
          </div>

          {/* Progress Steps */}
          <div className="flex items-center gap-4 mb-8">
            {[1, 2].map((s) => (
              <div key={s} className="flex items-center">
                <div
                  className={cn(
                    "flex h-8 w-8 items-center justify-center rounded-full text-sm font-medium transition-colors",
                    step >= s
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted text-muted-foreground"
                  )}
                >
                  {step > s ? <Check className="h-4 w-4" /> : s}
                </div>
                {s < 2 && (
                  <div
                    className={cn(
                      "ml-4 h-0.5 w-16",
                      step > s ? "bg-primary" : "bg-muted"
                    )}
                  />
                )}
              </div>
            ))}
          </div>

          {error && (
            <div className="mb-6 flex items-start gap-3 rounded-xl border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">
              <AlertCircle className="h-4 w-4 mt-0.5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Social Login */}
          {step === 1 && (
            <>
              <div className="grid grid-cols-2 gap-4 mb-6">
                <Button
                  type="button"
                  variant="outline"
                  className="h-12 rounded-xl"
                  disabled={!!oauthLoading || isLoading}
                  onClick={async () => {
                    setError(null);
                    setOauthLoading('google');
                    try {
                      await loginWithGoogle();
                    } catch (err: unknown) {
                      setError(err instanceof Error ? err.message : 'Google sign-up failed');
                      setOauthLoading(null);
                    }
                  }}
                >
                  {oauthLoading === 'google' ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Globe className="h-5 w-5 mr-2" />}
                  Google
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  className="h-12 rounded-xl"
                  disabled={!!oauthLoading || isLoading}
                  onClick={async () => {
                    setError(null);
                    setOauthLoading('github');
                    try {
                      await loginWithGitHub();
                    } catch (err: unknown) {
                      setError(err instanceof Error ? err.message : 'GitHub sign-up failed');
                      setOauthLoading(null);
                    }
                  }}
                >
                  {oauthLoading === 'github' ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <FaGithub className="h-5 w-5 mr-2" />}
                  GitHub
                </Button>
              </div>

              <div className="relative mb-6">
                <div className="absolute inset-0 flex items-center">
                  <span className="w-full border-t" />
                </div>
                <div className="relative flex justify-center text-xs uppercase">
                  <span className="bg-background px-2 text-muted-foreground">
                    Or continue with email
                  </span>
                </div>
              </div>
            </>
          )}

          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-5">
              {step === 1 && (
                <>
                  {/* Name Fields */}
                  <div className="grid grid-cols-2 gap-4">
                    <FormField
                      control={form.control}
                      name="firstName"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>First Name</FormLabel>
                          <FormControl>
                            <div className="relative">
                              <User className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
                              <Input
                                placeholder="John"
                                className="h-12 pl-10 rounded-xl"
                                {...field}
                              />
                            </div>
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="lastName"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Last Name</FormLabel>
                          <FormControl>
                            <Input
                              placeholder="Doe"
                              className="h-12 rounded-xl"
                              {...field}
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>

                  <FormField
                    control={form.control}
                    name="email"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Email</FormLabel>
                        <FormControl>
                          <div className="relative">
                            <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
                            <Input
                              placeholder="name@company.com"
                              className="h-12 pl-10 rounded-xl"
                              {...field}
                            />
                          </div>
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="company"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Company (Optional)</FormLabel>
                        <FormControl>
                          <div className="relative">
                            <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
                            <Input
                              placeholder="Acme Inc."
                              className="h-12 pl-10 rounded-xl"
                              {...field}
                            />
                          </div>
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <Button
                    type="button"
                    onClick={() => setStep(2)}
                    className="w-full h-12 rounded-xl bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500"
                  >
                    Continue
                    <ArrowRight className="h-5 w-5 ml-2" />
                  </Button>
                </>
              )}

              {step === 2 && (
                <>
                  {/* Plan Selection */}
                  <FormField
                    control={form.control}
                    name="plan"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Choose a Plan</FormLabel>
                        <div className="grid gap-3 mt-2">
                          {plans.map((plan) => (
                            <div
                              key={plan.id}
                              onClick={() => field.onChange(plan.id)}
                              className={cn(
                                "relative flex cursor-pointer rounded-xl border p-4 transition-all",
                                field.value === plan.id
                                  ? "border-primary bg-primary/5 ring-2 ring-primary"
                                  : "border-muted hover:border-primary/50"
                              )}
                            >
                              <div className="flex-1">
                                <div className="flex items-center justify-between">
                                  <span className="font-semibold">{plan.name}</span>
                                  <span className="text-lg font-bold">{plan.price}</span>
                                </div>
                                <p className="text-sm text-muted-foreground mt-1">
                                  {plan.description}
                                </p>
                              </div>
                              {field.value === plan.id && (
                                <div className="absolute right-4 top-4">
                                  <div className="h-5 w-5 rounded-full bg-primary flex items-center justify-center">
                                    <Check className="h-3 w-3 text-primary-foreground" />
                                  </div>
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="password"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Password</FormLabel>
                        <FormControl>
                          <div className="relative">
                            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
                            <Input
                              type={showPassword ? 'text' : 'password'}
                              placeholder="••••••••"
                              className="h-12 pl-10 pr-10 rounded-xl"
                              {...field}
                            />
                            <button
                              type="button"
                              onClick={() => setShowPassword(!showPassword)}
                              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                            >
                              {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                            </button>
                          </div>
                        </FormControl>
                        {/* Password Strength Indicator */}
                        {password && (
                          <div className="mt-2">
                            <div className="flex gap-1">
                              {[1, 2, 3, 4, 5].map((level) => (
                                <div
                                  key={level}
                                  className={cn(
                                    "h-1 flex-1 rounded-full transition-colors",
                                    passwordStrength >= level
                                      ? passwordStrength <= 2
                                        ? "bg-red-500"
                                        : passwordStrength <= 3
                                        ? "bg-yellow-500"
                                        : "bg-green-500"
                                      : "bg-muted"
                                  )}
                                />
                              ))}
                            </div>
                            <p className="text-xs text-muted-foreground mt-1">
                              {passwordStrength <= 2 && "Weak password"}
                              {passwordStrength === 3 && "Moderate password"}
                              {passwordStrength >= 4 && "Strong password"}
                            </p>
                          </div>
                        )}
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="confirmPassword"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Confirm Password</FormLabel>
                        <FormControl>
                          <div className="relative">
                            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
                            <Input
                              type={showConfirmPassword ? 'text' : 'password'}
                              placeholder="••••••••"
                              className="h-12 pl-10 pr-10 rounded-xl"
                              {...field}
                            />
                            <button
                              type="button"
                              onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                            >
                              {showConfirmPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                            </button>
                          </div>
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="acceptTerms"
                    render={({ field }) => (
                      <FormItem className="flex items-start space-x-3 space-y-0">
                        <FormControl>
                          <Checkbox
                            checked={field.value}
                            onCheckedChange={field.onChange}
                          />
                        </FormControl>
                        <div className="space-y-1 leading-none">
                          <FormLabel className="text-sm font-normal">
                            I agree to the{' '}
                            <Link href="/terms" className="text-primary hover:underline">
                              Terms of Service
                            </Link>{' '}
                            and{' '}
                            <Link href="/privacy" className="text-primary hover:underline">
                              Privacy Policy
                            </Link>
                          </FormLabel>
                          <FormMessage />
                        </div>
                      </FormItem>
                    )}
                  />

                  <div className="flex gap-4">
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => setStep(1)}
                      className="flex-1 h-12 rounded-xl"
                    >
                      Back
                    </Button>
                    <Button
                      type="submit"
                      disabled={isLoading}
                      className="flex-1 h-12 rounded-xl bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500"
                    >
                      {isLoading ? (
                        <>
                          <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                          Creating...
                        </>
                      ) : (
                        <>
                          Create Account
                          <ArrowRight className="h-5 w-5 ml-2" />
                        </>
                      )}
                    </Button>
                  </div>
                </>
              )}
            </form>
          </Form>

          {/* Sign In Link */}
          <p className="text-center mt-6 text-muted-foreground">
            Already have an account?{' '}
            <Link href="/login" className="text-primary font-medium hover:underline">
              Sign in
            </Link>
          </p>
        </motion.div>
      </div>

      {/* Right Panel - Visual */}
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-purple-600 via-indigo-600 to-blue-600" />
        <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-10" />
        
        {/* Animated Elements */}
        <motion.div
          className="absolute top-1/3 left-1/4 w-80 h-80 bg-white/10 rounded-full blur-3xl"
          animate={{
            x: [0, 30, 0],
            y: [0, -40, 0],
          }}
          transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
        />
        <motion.div
          className="absolute bottom-1/4 right-1/3 w-96 h-96 bg-blue-500/20 rounded-full blur-3xl"
          animate={{
            x: [0, -50, 0],
            y: [0, 30, 0],
          }}
          transition={{ duration: 10, repeat: Infinity, ease: "easeInOut" }}
        />

        {/* Content */}
        <div className="relative z-10 flex flex-col justify-center items-center text-white p-16">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5 }}
            className="text-center"
          >
            <h2 className="text-4xl font-bold mb-6">
              Join 10,000+ teams using MultiAgent AI
            </h2>
            <p className="text-xl text-white/70 mb-12 max-w-md mx-auto">
              Build intelligent workflows, automate tasks, and scale your operations with AI agents.
            </p>

            {/* Testimonial */}
            <div className="glass-morphism rounded-2xl p-6 max-w-md mx-auto">
              <p className="text-lg mb-4">
                &ldquo;MultiAgent AI transformed how we handle customer support. 
                Our response time dropped by 80%.&rdquo;
              </p>
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-full bg-white/20" />
                <div className="text-left">
                  <p className="font-semibold">Sarah Chen</p>
                  <p className="text-sm text-white/60">CTO, TechCorp</p>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
