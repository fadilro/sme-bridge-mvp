import React, { createContext, useContext, useEffect, useState } from 'react';
import { apiClient } from '../api/client';

interface Sme {
  id: string;
  company_name: string;
  plc_id: string;
}

interface SmeContextValue {
  smes: Sme[];
  selectedSmeId: string;
  setSelectedSmeId: (id: string) => void;
  loading: boolean;
}

const SmeContext = createContext<SmeContextValue>({
  smes: [],
  selectedSmeId: '',
  setSelectedSmeId: () => {},
  loading: true,
});

export const SmeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [smes, setSmes] = useState<Sme[]>([]);
  const [selectedSmeId, setSelectedSmeId] = useState<string>('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiClient.get<Sme[]>('/smes').then((res) => {
      setSmes(res.data);
      if (res.data.length > 0) {
        setSelectedSmeId(res.data[0].id);
      }
    }).catch(console.error).finally(() => setLoading(false));
  }, []);

  return (
    <SmeContext.Provider value={{ smes, selectedSmeId, setSelectedSmeId, loading }}>
      {children}
    </SmeContext.Provider>
  );
};

export const useSme = () => useContext(SmeContext);
