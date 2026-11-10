import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { Search, SlidersHorizontal, X } from 'lucide-react';
import { api } from '../services/api';
import ProductCard from '../components/ProductCard';

const CATEGORY_LABELS = {
  todos: 'Todos',
  postres: 'Postres',
  snacks: 'Snacks',
  bebidas: 'Bebidas',
};

export default function CatalogoPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const activeCategory = searchParams.get('cat') || 'todos';
  const searchQuery = searchParams.get('q') || '';

  const [localSearch, setLocalSearch] = useState(searchQuery);

  useEffect(() => {
    setLoading(true);
    setError(null);
    const params = {};
    if (activeCategory && activeCategory !== 'todos') params.category = activeCategory;
    if (searchQuery) params.search = searchQuery;

    api.getProducts(params)
      .then(setProducts)
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, [activeCategory, searchQuery]);

  useEffect(() => {
    api.getCategories().then(setCategories).catch(() => {});
  }, []);

  const handleCategoryClick = (slug) => {
    const params = {};
    if (slug !== 'todos') params.cat = slug;
    if (localSearch) params.q = localSearch;
    setSearchParams(params);
  };

  const handleSearch = (e) => {
    e.preventDefault();
    const params = {};
    if (activeCategory !== 'todos') params.cat = activeCategory;
    if (localSearch.trim()) params.q = localSearch.trim();
    setSearchParams(params);
  };

  const clearSearch = () => {
    setLocalSearch('');
    const params = {};
    if (activeCategory !== 'todos') params.cat = activeCategory;
    setSearchParams(params);
  };

  return (
    <div className="min-h-screen py-10 px-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="font-display font-extrabold text-3xl sm:text-4xl text-[#4B2E1F] mb-2">
            Catálogo Neifit
          </h1>
          <p className="text-[#7A4E2D]/70">Postres artesanales, snacks naturales y bebidas seleccionadas.</p>
        </div>

        {/* Search bar */}
        <form onSubmit={handleSearch} className="flex gap-2 mb-8 max-w-xl">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#7A4E2D]/50" />
            <input
              type="search"
              value={localSearch}
              onChange={e => setLocalSearch(e.target.value)}
              placeholder="Buscar productos..."
              className="w-full pl-10 pr-4 py-2.5 bg-[#FFF8F2] border border-[#7A4E2D]/25 rounded-xl text-[#4B2E1F] placeholder-[#7A4E2D]/40 focus:outline-none focus:ring-2 focus:ring-[#7A4E2D]/30 text-sm"
            />
          </div>
          <button type="submit" className="btn-primary px-4 py-2.5">
            Buscar
          </button>
          {(searchQuery) && (
            <button type="button" onClick={clearSearch} className="p-2.5 bg-[#FFF8F2] border border-[#7A4E2D]/25 rounded-xl text-[#7A4E2D] hover:bg-[#F6E7D8]">
              <X className="w-4 h-4" />
            </button>
          )}
        </form>

        {/* Category Filter Tabs */}
        <div className="flex flex-wrap gap-2 mb-8">
          {[{ slug: 'todos', name: 'Todos' }, ...categories].map(cat => (
            <button
              key={cat.slug || 'todos'}
              onClick={() => handleCategoryClick(cat.slug || 'todos')}
              className={`px-4 py-2 rounded-full text-sm font-semibold transition-all ${
                activeCategory === (cat.slug || 'todos')
                  ? 'bg-[#7A4E2D] text-white shadow-sm'
                  : 'bg-[#FFF8F2] text-[#7A4E2D] border border-[#7A4E2D]/25 hover:bg-[#F6E7D8]'
              }`}
            >
              {cat.name}
            </button>
          ))}
        </div>

        {/* Active filters info */}
        {(searchQuery || activeCategory !== 'todos') && (
          <div className="flex flex-wrap gap-2 mb-6 items-center text-sm text-[#7A4E2D]/70">
            <SlidersHorizontal className="w-4 h-4" />
            <span>Filtrando por:</span>
            {activeCategory !== 'todos' && (
              <span className="badge-pink">{CATEGORY_LABELS[activeCategory] || activeCategory}</span>
            )}
            {searchQuery && (
              <span className="badge-pink">"{searchQuery}"</span>
            )}
          </div>
        )}

        {/* Products Grid */}
        {loading ? (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {[...Array(8)].map((_, i) => (
              <div key={i} className="card-cream animate-pulse">
                <div className="aspect-[4/3] bg-[#F6E7D8] rounded-t-2xl" />
                <div className="p-4 space-y-2">
                  <div className="h-3 bg-[#F6E7D8] rounded w-20" />
                  <div className="h-5 bg-[#F6E7D8] rounded w-full" />
                  <div className="h-4 bg-[#F6E7D8] rounded w-3/4" />
                </div>
              </div>
            ))}
          </div>
        ) : error ? (
          <div className="text-center py-20">
            <p className="text-red-600 mb-4">{error}</p>
            <button onClick={() => window.location.reload()} className="btn-primary">Reintentar</button>
          </div>
        ) : products.length === 0 ? (
          <div className="text-center py-20">
            <p className="text-5xl mb-4">🔍</p>
            <p className="text-[#7A4E2D] font-semibold text-lg mb-2">No encontramos productos</p>
            <p className="text-[#7A4E2D]/60 mb-6">Prueba con otra categoría o elimina el filtro de búsqueda.</p>
            <button onClick={() => setSearchParams({})} className="btn-outline">Ver todos los productos</button>
          </div>
        ) : (
          <>
            <p className="text-sm text-[#7A4E2D]/60 mb-5">
              {products.length} producto{products.length !== 1 ? 's' : ''} encontrado{products.length !== 1 ? 's' : ''}
            </p>
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {products.map(p => <ProductCard key={p.id} product={p} />)}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

