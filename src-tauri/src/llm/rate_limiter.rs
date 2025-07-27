use std::collections::VecDeque;
use std::time::{Duration, Instant};

/// Simple token bucket rate limiter
#[derive(Debug)]
pub struct RateLimiter {
    tokens: f64,
    capacity: f64,
    refill_rate: f64, // tokens per second
    last_refill: Instant,
    request_history: VecDeque<Instant>,
    window_duration: Duration,
}

impl RateLimiter {
    pub fn new(requests_per_minute: u32) -> Self {
        let capacity = requests_per_minute as f64;
        Self {
            tokens: capacity,
            capacity,
            refill_rate: capacity / 60.0, // tokens per second
            last_refill: Instant::now(),
            request_history: VecDeque::new(),
            window_duration: Duration::from_secs(60),
        }
    }

    pub fn new_unlimited() -> Self {
        Self {
            tokens: f64::MAX,
            capacity: f64::MAX,
            refill_rate: f64::MAX,
            last_refill: Instant::now(),
            request_history: VecDeque::new(),
            window_duration: Duration::from_secs(60),
        }
    }

    pub fn try_acquire(&mut self, tokens_needed: f64) -> bool {
        self.refill();
        self.clean_history();
        
        if self.tokens >= tokens_needed {
            self.tokens -= tokens_needed;
            self.request_history.push_back(Instant::now());
            true
        } else {
            false
        }
    }

    pub fn time_until_available(&mut self, tokens_needed: f64) -> Duration {
        self.refill();
        
        if self.tokens >= tokens_needed {
            Duration::ZERO
        } else {
            let tokens_deficit = tokens_needed - self.tokens;
            let seconds_needed = tokens_deficit / self.refill_rate;
            Duration::from_secs_f64(seconds_needed)
        }
    }

    pub fn requests_in_current_window(&self) -> usize {
        let cutoff = Instant::now() - self.window_duration;
        self.request_history
            .iter()
            .filter(|&&time| time > cutoff)
            .count()
    }

    pub fn is_unlimited(&self) -> bool {
        self.capacity == f64::MAX
    }

    fn refill(&mut self) {
        let now = Instant::now();
        let elapsed = now.duration_since(self.last_refill).as_secs_f64();
        let tokens_to_add = elapsed * self.refill_rate;
        
        self.tokens = (self.tokens + tokens_to_add).min(self.capacity);
        self.last_refill = now;
    }

    fn clean_history(&mut self) {
        let cutoff = Instant::now() - self.window_duration;
        while let Some(&front) = self.request_history.front() {
            if front <= cutoff {
                self.request_history.pop_front();
            } else {
                break;
            }
        }
    }
}