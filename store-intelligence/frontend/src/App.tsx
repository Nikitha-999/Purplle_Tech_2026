import { AnimatePresence, motion } from 'framer-motion';
import { Route, Routes, useLocation } from 'react-router-dom';
import { useState } from 'react';
import { QueryClient, useQueryClient } from '@tanstack/react-query';
import { Sidebar } from './components/Sidebar';
import { Topbar } from './components/Topbar';
import OverviewPage from './pages/overview';
import FunnelPage from './pages/funnel';
import HeatmapPage from './pages/heatmap';
import AnomaliesPage from './pages/anomalies';
import PipelinePage from './pages/pipeline';
import ViewerPage from './pages/viewer';
import LayoutPage from './pages/layout';
import CommandCenterPage from './pages/command-center';
import InsightsPage from './pages/insights';
import ReplayPage from './pages/replay';
import { useDarkMode } from './hooks/useDarkMode';

const routes: Array<{ path: string; label: string; icon: 'Grid' | 'TrendingUp' | 'MapPin' | 'AlertTriangle' | 'Server' | 'Video' | 'Layers' | 'Monitor' | 'Lightbulb' | 'PlayCircle' }> = [
  { path: '/', label: 'Dashboard', icon: 'Grid' },
  { path: '/command-center', label: 'Command Center', icon: 'Monitor' },
  { path: '/insights', label: 'Insights', icon: 'Lightbulb' },
  { path: '/funnel', label: 'Funnel', icon: 'TrendingUp' },
  { path: '/heatmap', label: 'Heatmap', icon: 'MapPin' },
  { path: '/anomalies', label: 'Anomalies', icon: 'AlertTriangle' },
  { path: '/replay', label: 'Replay', icon: 'PlayCircle' },
  { path: '/pipeline', label: 'Pipeline', icon: 'Server' },
  { path: '/viewer', label: 'Viewer', icon: 'Video' },
  { path: '/layout', label: 'Layout', icon: 'Layers' },
];

function App() {
  const location = useLocation();
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [currentStore, setCurrentStore] = useState('ST1008');
  const [selectedDate, setSelectedDate] = useState('2026-04-10');
  const { darkMode, setDarkMode } = useDarkMode();
  const queryClient = useQueryClient();

  const refreshAll = () => {
    queryClient.invalidateQueries();
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100">
      <div className="relative flex min-h-screen overflow-hidden">
        <Sidebar
          routes={routes}
          open={drawerOpen}
          onOpenChange={setDrawerOpen}
        />

        <div className="flex-1">
          <Topbar
            currentStore={currentStore}
            onStoreChange={setCurrentStore}
            selectedDate={selectedDate}
            onDateChange={setSelectedDate}
            darkMode={darkMode}
            onToggleTheme={() => setDarkMode(!darkMode)}
            onRefresh={refreshAll}
            onMenuClick={() => setDrawerOpen(true)}
          />

          <main className="min-h-[calc(100vh-96px)] p-4 sm:p-6 lg:p-8">
            <AnimatePresence mode="wait">
              <motion.div
                key={location.pathname}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.25 }}
              >
                <Routes location={location}>
                  <Route
                    path="/"
                    element={<OverviewPage storeId={currentStore} date={selectedDate} />}
                  />
                  <Route
                    path="/command-center"
                    element={<CommandCenterPage storeId={currentStore} date={selectedDate} />}
                  />
                  <Route
                    path="/insights"
                    element={<InsightsPage storeId={currentStore} date={selectedDate} />}
                  />
                  <Route
                    path="/funnel"
                    element={<FunnelPage storeId={currentStore} date={selectedDate} />}
                  />
                  <Route
                    path="/heatmap"
                    element={<HeatmapPage storeId={currentStore} date={selectedDate} />}
                  />
                  <Route
                    path="/anomalies"
                    element={<AnomaliesPage storeId={currentStore} date={selectedDate} />}
                  />
                  <Route path="/replay" element={<ReplayPage storeId={currentStore} date={selectedDate} />} />
                  <Route path="/pipeline" element={<PipelinePage />} />
                  <Route path="/viewer" element={<ViewerPage />} />
                  <Route path="/layout" element={<LayoutPage />} />
                </Routes>
              </motion.div>
            </AnimatePresence>
          </main>
        </div>
      </div>
    </div>
  );
}

export default App;
