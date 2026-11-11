import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { CartProvider } from './context/CartContext';
import AppRouter from './router/AppRouter';
import { ModulesMenuProvider } from './components/SiteLayout';
import './index.css';
import { ThemeProvider } from './context/ThemeContext';

export default function App() {
  return (
    <BrowserRouter>
      <ThemeProvider><AuthProvider>
        <CartProvider>
          <ModulesMenuProvider>
            <AppRouter />
          </ModulesMenuProvider>
        </CartProvider>
      </AuthProvider></ThemeProvider>
    </BrowserRouter>
  );
}

