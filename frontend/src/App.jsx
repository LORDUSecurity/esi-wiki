import { useEffect } from 'react';
import { Route, Routes, useLocation } from 'react-router-dom';
import Nav from './components/Nav';
import Footer from './components/Footer';
import Home from './pages/Home';
import Programmes from './pages/Programmes';
import ModuleDetail from './pages/ModuleDetail';
import CampusLife from './pages/CampusLife';
import EsiHub from './pages/EsiHub';
import Faq from './pages/Faq';
import About from './pages/About';
import Contact from './pages/Contact';
import Assistant from './pages/Assistant';

function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'instant' });
  }, [pathname]);
  return null;
}

export default function App() {
  return (
    <div className="relative min-h-screen bg-ink-950">
      <ScrollToTop />
      <Nav />
      <main>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/programmes" element={<Programmes />} />
          <Route path="/programmes/:slug" element={<ModuleDetail />} />
          <Route path="/campus" element={<CampusLife />} />
          <Route path="/esihub" element={<EsiHub />} />
          <Route path="/faq" element={<Faq />} />
          <Route path="/a-propos" element={<About />} />
          <Route path="/contact" element={<Contact />} />
          <Route path="/assistant" element={<Assistant />} />
          <Route path="*" element={<Home />} />
        </Routes>
      </main>
      <Footer />
    </div>
  );
}
