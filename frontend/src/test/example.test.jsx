import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import App from '../App'

describe('App Component', () => {
  it('renders without crashing', () => {
    render(<App />)
    // Basic smoke test - just ensure the app renders
    expect(document.body).toBeTruthy()
  })
})

// Example of testing a simple utility function
describe('Example utilities', () => {
  it('should demonstrate basic testing', () => {
    const sum = (a, b) => a + b
    expect(sum(2, 3)).toBe(5)
  })
})

// Example of testing with React Testing Library
describe('React Testing Library example', () => {
  it('should find elements by role', () => {
    render(<button>Click me</button>)
    const button = screen.getByRole('button', { name: /click me/i })
    expect(button).toBeInTheDocument()
  })
})