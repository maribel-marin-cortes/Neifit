import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { api } from '../services/api';

export const DEFAULT_THEME = {
  primary_color:'#7A4E2D', secondary_color:'#5F8D4E', accent_color:'#D98CA4',
  background_color:'#F6E7D8', surface_color:'#FFF8F2', text_color:'#4B2E1F',
  logo_url:null, icon_url:null, cover_url:null, heading_font:'Poppins', body_font:'Inter',
  border_radius:16, button_style:'solido', published:true,
};

const ThemeContext = createContext(null);

function applyTheme(theme) {
  const root = document.documentElement;
  const vars = {
    '--color-primary':theme.primary_color, '--color-secondary':theme.secondary_color,
    '--color-accent':theme.accent_color, '--color-background':theme.background_color,
    '--color-surface':theme.surface_color, '--color-text':theme.text_color,
    '--font-heading':theme.heading_font, '--font-body':theme.body_font,
    '--radius-company':`${theme.border_radius}px`,
  };
  Object.entries(vars).forEach(([key,value]) => root.style.setProperty(key,value));
  root.dataset.buttonStyle = theme.button_style;
}

export function ThemeProvider({ children }) {
  const [theme,setThemeState] = useState(DEFAULT_THEME);
  const [loading,setLoading] = useState(true);
  async function reload() {
    setLoading(true);
    try {
      const loaded = await api.getCompanyTheme();
      const next = { ...DEFAULT_THEME, ...loaded };
      setThemeState(next); applyTheme(next);
    } catch { setThemeState(DEFAULT_THEME); applyTheme(DEFAULT_THEME); }
    finally { setLoading(false); }
  }
  useEffect(() => {
    reload();
    window.addEventListener('neifit-company-change',reload);
    return () => window.removeEventListener('neifit-company-change',reload);
  },[]);
  const preview = next => { const value={...theme,...next}; setThemeState(value); applyTheme(value); };
  const save = async next => { const saved=await api.updateCompanyTheme({...theme,...next}); preview(saved); return saved; };
  const value = useMemo(() => ({theme,loading,preview,save,reload}),[theme,loading]);
  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useCompanyTheme() {
  const value=useContext(ThemeContext);
  if (!value) throw new Error('useCompanyTheme requiere ThemeProvider');
  return value;
}
