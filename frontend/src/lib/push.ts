export interface BrowserPushSubscription {
  endpoint: string;
  keys: {
    p256dh: string;
    auth: string;
  };
  user_agent?: string;
  platform?: string;
}

export interface PushEnvironment {
  supported: boolean;
  permission: NotificationPermission | 'unsupported';
  is_ios: boolean;
  is_standalone: boolean;
  requires_install: boolean;
}

function urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);

  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }

  return outputArray;
}

function detectIOS(): boolean {
  if (typeof navigator === 'undefined') {
    return false;
  }

  return /iPad|iPhone|iPod/.test(navigator.userAgent)
    || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
}

export function getPushEnvironment(): PushEnvironment {
  if (
    typeof window === 'undefined'
    || typeof navigator === 'undefined'
    || !('serviceWorker' in navigator)
    || !('PushManager' in window)
    || !('Notification' in window)
  ) {
    return {
      supported: false,
      permission: 'unsupported',
      is_ios: false,
      is_standalone: false,
      requires_install: false,
    };
  }

  const isIOS = detectIOS();
  const isStandalone = window.matchMedia('(display-mode: standalone)').matches
    || (window.navigator as Navigator & { standalone?: boolean }).standalone === true;

  return {
    supported: true,
    permission: Notification.permission,
    is_ios: isIOS,
    is_standalone: isStandalone,
    requires_install: isIOS && !isStandalone,
  };
}

async function ensureRegistration(): Promise<ServiceWorkerRegistration> {
  const registration = await navigator.serviceWorker.register('/sw.js');
  return navigator.serviceWorker.ready.then(() => registration);
}

export async function getExistingSubscription(): Promise<PushSubscription | null> {
  const env = getPushEnvironment();
  if (!env.supported) {
    return null;
  }

  const registration = await ensureRegistration();
  return registration.pushManager.getSubscription();
}

export async function createPushSubscription(vapidPublicKey: string): Promise<BrowserPushSubscription> {
  const env = getPushEnvironment();
  if (!env.supported) {
    throw new Error('Push notifications are not supported on this device.');
  }
  if (env.requires_install) {
    throw new Error('Install the app to your home screen before enabling notifications on iPhone.');
  }

  const permission = Notification.permission === 'granted'
    ? 'granted'
    : await Notification.requestPermission();
  if (permission !== 'granted') {
    throw new Error('Notification permission was not granted.');
  }

  const registration = await ensureRegistration();
  const existing = await registration.pushManager.getSubscription();
  const subscription = existing ?? await registration.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: urlBase64ToUint8Array(vapidPublicKey),
  });

  const json = subscription.toJSON();
  const keys = json.keys;
  if (!json.endpoint || !keys?.p256dh || !keys?.auth) {
    throw new Error('Browser returned an incomplete push subscription.');
  }

  return {
    endpoint: json.endpoint,
    keys: {
      p256dh: keys.p256dh,
      auth: keys.auth,
    },
    user_agent: navigator.userAgent,
    platform: detectIOS() ? 'ios' : navigator.platform || 'web',
  };
}

export async function removePushSubscription(): Promise<string | null> {
  const subscription = await getExistingSubscription();
  if (!subscription) {
    return null;
  }

  const endpoint = subscription.endpoint;
  await subscription.unsubscribe();
  return endpoint;
}
