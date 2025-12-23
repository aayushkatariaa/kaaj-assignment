import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Applications from './pages/Applications'
import ApplicationForm from './pages/ApplicationForm'
import ApplicationDetail from './pages/ApplicationDetail'
import Lenders from './pages/Lenders'
import LenderDetail from './pages/LenderDetail'
import PDFIngestion from './pages/PDFIngestion'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="applications" element={<Applications />} />
        <Route path="applications/new" element={<ApplicationForm />} />
        <Route path="applications/:id" element={<ApplicationDetail />} />
        <Route path="lenders" element={<Lenders />} />
        <Route path="lenders/:id" element={<LenderDetail />} />
        <Route path="pdf-ingestion" element={<PDFIngestion />} />
      </Route>
    </Routes>
  )
}

export default App
