import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { CartProvider } from './context/CartContext';
import AppRouter from './router/AppRouter';
import { ModulesMenuProvider } from './components/SiteLayout';
import './index.css';

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <CartProvider>
          <ModulesMenuProvider>
            <AppRouter />
          </ModulesMenuProvider>
        </CartProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}

