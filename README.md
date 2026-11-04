# RFQ Auction System

## About the Project
This project is a simple RFQ (Request for Quotation) system with a British Auction feature. Buyers can create RFQs, and suppliers can submit their quotations. The system compares the quotes and displays supplier rankings based on the lowest price.

Live demo:- https://gocomet-rfq-auction.vercel.app

## Features
- User login with Admin, Buyer and Supplier roles.
- Create and manage RFQs.
- Submit and compare supplier quotations.
- Automatic L1, L2 and L3 rankings.
- British Auction automatic time extension.
- Forced closing time to stop bidding.
- Auction history and activity tracking.

## Technologies Used
- Frontend: React, TypeScript and Vite
- Backend: Python and FastAPI
- Database: SQLite
- SQLAlchemy
- WebSockets

## Project Structure
- `frontend` – Frontend application
- `backend` – Backend application and APIs
- `docs` – HLD and Database Schema documents

## Demo Login
- Admin: admin@demo.com (Password: admin123)
- Buyer: buyer@demo.com (Password: buyer123)
- Supplier: supplier@demo.com (Password: supplier123)

## Documentation
- High-Level Design (HLD): [`docs/HLD.pdf`](docs/HLD.pdf)
- Database Schema Design: [`docs/Database_Schema.pdf`](docs/Database_Schema.pdf)
