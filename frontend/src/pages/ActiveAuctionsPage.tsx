import React from 'react';
import { AuctionListingPage } from './AuctionListingPage';

export const ActiveAuctionsPage: React.FC = () => {
  return <AuctionListingPage activeOnly={true} />;
};
