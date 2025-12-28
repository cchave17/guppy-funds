# Guppy Funds Frontend

Modern, responsive web interface for the Guppy Funds personal finance management system.

## Tech Stack

- **Framework:** Next.js 14 (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS v4
- **UI Components:** shadcn/ui
- **State Management:**
  - Tanstack Query (React Query) for server state
  - Zustand for client state
- **Charts:** Recharts
- **Icons:** Lucide React

## Features

- **Dashboard:** Overview with key metrics, charts, and recent transactions
- **Transactions:** Comprehensive transaction list with filtering and pagination
- **Balances:** Account balances and net worth tracking
- **Merchants:** Browse and filter merchant directory
- **Import:** CSV file upload wizard for AMEX, Citi, and Wells Fargo
- **Dark Mode:** Automatic system preference detection
- **Responsive Design:** Mobile-first approach

## Getting Started

### Prerequisites

- Node.js 18+ and npm

### Development

```bash
# Install dependencies
npm install

# Run development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Environment Variables

Create a `.env.local` file:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Project Structure

```
frontend/
├── app/                    # Next.js 14 app directory
│   ├── page.tsx           # Dashboard
│   ├── transactions/
│   ├── balances/
│   ├── merchants/
│   ├── import/
│   ├── layout.tsx         # Root layout
│   └── globals.css        # Global styles
├── components/
│   ├── ui/                # shadcn/ui components
│   ├── dashboard/         # Dashboard-specific components
│   ├── charts/            # Chart components
│   └── layout/            # Layout components
├── hooks/                 # Custom React hooks
├── lib/
│   ├── api.ts            # API client
│   ├── types.ts          # TypeScript types
│   └── utils.ts          # Utility functions
└── public/               # Static assets
```
