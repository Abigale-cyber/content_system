#!/usr/bin/env node

// ============================================================================
// Follow Builders — Prepare Digest
// ============================================================================
// Gathers everything the LLM needs to produce a digest:
// - Fetches the central feeds (tweets + podcasts)
// - Loads prompt templates
// - Reads the user's config (language, delivery method)
// - Outputs a single JSON blob to stdout
//
// The LLM's ONLY job is to read this JSON, remix the content, and output
// the digest text. Everything else is handled here deterministically.
//
// Usage: node prepare-digest.js
// Output: JSON to stdout
// ============================================================================

import { readFile } from 'fs/promises';
import { existsSync } from 'fs';
import { join } from 'path';
import { homedir } from 'os';
import { execFile } from 'child_process';
import { promisify } from 'util';

// -- Constants ---------------------------------------------------------------

const USER_DIR = process.env.AI_DALABA_USER_DIR || join(homedir(), '.ai-dalaba');
const LEGACY_USER_DIR = join(homedir(), '.follow-builders');
const CONFIG_PATH = process.env.AI_DALABA_CONFIG_PATH || join(USER_DIR, 'config.json');
const LEGACY_CONFIG_PATH = join(LEGACY_USER_DIR, 'config.json');
const SCRIPT_DIR = decodeURIComponent(new URL('.', import.meta.url).pathname);
const SKILL_DIR = join(SCRIPT_DIR, '..');

const FEEDS = [
  {
    key: 'x',
    label: 'tweet',
    url: 'https://raw.githubusercontent.com/zarazhangrui/follow-builders/main/feed-x.json',
    localPath: join(SKILL_DIR, 'feed-x.json'),
    contentKey: 'x'
  },
  {
    key: 'podcasts',
    label: 'podcast',
    url: 'https://raw.githubusercontent.com/zarazhangrui/follow-builders/main/feed-podcasts.json',
    localPath: join(SKILL_DIR, 'feed-podcasts.json'),
    contentKey: 'podcasts'
  },
  {
    key: 'blogs',
    label: 'blog',
    url: 'https://raw.githubusercontent.com/zarazhangrui/follow-builders/main/feed-blogs.json',
    localPath: join(SKILL_DIR, 'feed-blogs.json'),
    contentKey: 'blogs'
  }
];

const PROMPT_FILES = [
  'summarize-podcast.md',
  'summarize-tweets.md',
  'summarize-blogs.md',
  'digest-intro.md',
  'translate.md'
];

const FETCH_TIMEOUT_MS = 12000;
const CURL_CONNECT_TIMEOUT_SECONDS = '10';
const CURL_MAX_TIME_SECONDS = '15';
const MAX_BUFFER_BYTES = 10 * 1024 * 1024;

// -- Fetch helpers -----------------------------------------------------------

const execFileAsync = promisify(execFile);

async function readTextIfExists(path) {
  try {
    return await readFile(path, 'utf-8');
  } catch {
    return null;
  }
}

async function fetchViaCurl(url) {
  const { stdout } = await execFileAsync(
    'curl',
    [
      '-fsSL',
      '--connect-timeout',
      CURL_CONNECT_TIMEOUT_SECONDS,
      '--max-time',
      CURL_MAX_TIME_SECONDS,
      '--retry',
      '1',
      '--retry-delay',
      '1',
      url
    ],
    { maxBuffer: MAX_BUFFER_BYTES }
  );
  return stdout;
}

async function fetchText(url) {
  try {
    const res = await fetch(url, {
      signal: AbortSignal.timeout(FETCH_TIMEOUT_MS)
    });
    if (res.ok) return await res.text();
  } catch {}

  try {
    return await fetchViaCurl(url);
  } catch {
    return null;
  }
}

async function fetchJSONWithLocalFallback(url, localPath) {
  const remoteText = await fetchText(url);
  if (remoteText) {
    try {
      return { data: JSON.parse(remoteText), source: 'remote' };
    } catch {}
  }

  const localText = await readTextIfExists(localPath);
  if (localText) {
    try {
      return { data: JSON.parse(localText), source: 'local' };
    } catch {}
  }

  return { data: null, source: null };
}

// -- Main --------------------------------------------------------------------

async function main() {
  const errors = [];

  // 1. Read user config
  let config = {
    language: 'en',
    frequency: 'daily',
    delivery: { method: 'stdout' }
  };
  if (existsSync(CONFIG_PATH)) {
    try {
      config = JSON.parse(await readFile(CONFIG_PATH, 'utf-8'));
    } catch (err) {
      errors.push(`Could not read config: ${err.message}`);
    }
  } else if (existsSync(LEGACY_CONFIG_PATH)) {
    try {
      config = JSON.parse(await readFile(LEGACY_CONFIG_PATH, 'utf-8'));
      errors.push('Using legacy follow-builders config as fallback');
    } catch (err) {
      errors.push(`Could not read legacy config: ${err.message}`);
    }
  }

  // 2. Fetch feeds with fast remote timeouts and local fallback.
  const feedResults = await Promise.all(
    FEEDS.map(feed => fetchJSONWithLocalFallback(feed.url, feed.localPath))
  );

  const feeds = {};
  for (let i = 0; i < FEEDS.length; i += 1) {
    const meta = FEEDS[i];
    const result = feedResults[i];
    feeds[meta.key] = result.data;

    if (!result.data) {
      errors.push(`Could not load ${meta.label} feed`);
    } else if (result.source === 'local') {
      errors.push(`Using local cached ${meta.label} feed`);
    }
  }

  // 3. Load prompts with priority: user custom > local default > remote fallback.
  // Local-first keeps cron runs fast and predictable; remote is only a last-resort fallback.
  const prompts = {};
  const localPromptsDir = join(SKILL_DIR, 'prompts');
  const userPromptsDir = join(USER_DIR, 'prompts');

  await Promise.all(
    PROMPT_FILES.map(async filename => {
      const key = filename.replace('.md', '').replace(/-/g, '_');
      const userPath = join(userPromptsDir, filename);
      const localPath = join(localPromptsDir, filename);

      if (existsSync(userPath)) {
        prompts[key] = await readFile(userPath, 'utf-8');
        return;
      }

      const localText = await readTextIfExists(localPath);
      if (localText) {
        prompts[key] = localText;
        return;
      }

      const remote = await fetchText(`https://raw.githubusercontent.com/zarazhangrui/follow-builders/main/prompts/${filename}`);
      if (remote) {
        prompts[key] = remote;
        errors.push(`Using remote fallback prompt: ${filename}`);
        return;
      }

      errors.push(`Could not load prompt: ${filename}`);
    })
  );

  const feedX = feeds.x;
  const feedPodcasts = feeds.podcasts;
  const feedBlogs = feeds.blogs;

  // 4. Build the output — everything the LLM needs in one blob
  const output = {
    status: 'ok',
    generatedAt: new Date().toISOString(),

    // User preferences
    config: {
      language: config.language || 'en',
      frequency: config.frequency || 'daily',
      delivery: config.delivery || { method: 'stdout' }
    },

    // Content to remix
    podcasts: feedPodcasts?.podcasts || [],
    x: feedX?.x || [],
    blogs: feedBlogs?.blogs || [],

    // Stats for the LLM to reference
    stats: {
      podcastEpisodes: feedPodcasts?.podcasts?.length || 0,
      xBuilders: feedX?.x?.length || 0,
      totalTweets: (feedX?.x || []).reduce((sum, a) => sum + a.tweets.length, 0),
      blogPosts: feedBlogs?.blogs?.length || 0,
      feedGeneratedAt: feedX?.generatedAt || feedPodcasts?.generatedAt || feedBlogs?.generatedAt || null
    },

    // Prompts — the LLM reads these and follows the instructions
    prompts,

    // Non-fatal errors
    errors: errors.length > 0 ? errors : undefined
  };

  console.log(JSON.stringify(output, null, 2));
}

main().catch(err => {
  console.error(JSON.stringify({
    status: 'error',
    message: err.message
  }));
  process.exit(1);
});
