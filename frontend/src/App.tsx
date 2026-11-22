import { BrowserRouter, Route, Routes } from 'react-router-dom';
import { Layout } from './components/layout/Layout';
import { BusquedaProvider } from './context/BusquedaContext';
import { AdminPage } from './pages/AdminPage';
import { AlgoritmosPage } from './pages/AlgoritmosPage';
import { BuscarPage } from './pages/BuscarPage';
import { CuestionarioPage } from './pages/CuestionarioPage';
import { CompararPage } from './pages/CompararPage';
import { HomePage } from './pages/HomePage';
import { NotFoundPage } from './pages/NotFoundPage';
import { ResultadosPage } from './pages/ResultadosPage';

export default function App() {
  return (
    <BusquedaProvider>
      <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<HomePage />} />
            <Route path="buscar" element={<BuscarPage />} />
            <Route path="cuestionario" element={<CuestionarioPage />} />
            <Route path="resultados" element={<ResultadosPage />} />
            <Route path="comparar" element={<CompararPage />} />
            <Route path="algoritmos" element={<AlgoritmosPage />} />
            <Route path="admin" element={<AdminPage />} />
            <Route path="*" element={<NotFoundPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </BusquedaProvider>
  );
}
