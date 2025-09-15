"use client";
import { useState } from 'react';
import Link from 'next/link';
import { useAuth } from '@/context/AuthContext';
import TeamSelector from '@/components/TeamSelector';
import api from '@/services/api';

export default function CadastroPage() {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    nome_completo: '',
    time_favorito_id: null,
    foto_perfil: null,
  });
  const { register } = useAuth();
  
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleFileChange = (e) => {
    setFormData(prev => ({ ...prev, foto_perfil: e.target.files[0] }));
  };

  const handleNextStep = (e) => {
    e.preventDefault();
    setStep(2);
  };
  
  const handleFinalSubmit = (teamId) => {
    const finalData = { ...formData, time_favorito_id: teamId };
    
    // A função de upload e registro foi movida para dentro desta.
    const executeRegistration = async (dataToRegister) => {
        if (dataToRegister.foto_perfil && dataToRegister.foto_perfil instanceof File) {
            const fileData = new FormData();
            fileData.append('file', dataToRegister.foto_perfil);
            try {
                const uploadResponse = await api.post('/upload/profile-picture', fileData, {
                    headers: { 'Content-Type': 'multipart/form-data' },
                });
                dataToRegister.foto_perfil = uploadResponse.data.file_url;
            } catch (error) {
                console.error("Erro no upload da imagem:", error);
                return;
            }
        }
        
        await register(dataToRegister);
    }

    executeRegistration(finalData);
  }

  return (
    <div
      className="flex flex-col items-center justify-center min-h-screen p-6 text-white antialiased"
      style={{
        backgroundImage:
          "linear-gradient(rgba(10, 37, 64, 0.85), rgba(19, 59, 92, 0.95)), url('https://images.unsplash.com/photo-1519861531473-9200262188bf?q=80&w=2071&auto-format&fit=crop')",
        backgroundSize: 'cover',
        backgroundPosition: 'center',
      }}
    >
      <div className="w-full max-w-md bg-[#0A2540]/80 backdrop-blur-lg border border-gray-700 rounded-2xl shadow-2xl p-8">
        {step === 1 && (
          <>
            <div className="text-center mb-8">
              <h1 className="text-4xl font-bold tracking-tighter mb-2">Crie sua Conta</h1>
              <p className="text-gray-400">Passo 1 de 2: Suas informações</p>
            </div>
            <form className="space-y-4" onSubmit={handleNextStep}>
                {/* O formulário da Etapa 1 permanece igual */}
                <div>
                    <label className="block text-sm font-medium text-gray-300">Username</label>
                    <input type="text" name="username" required onChange={handleChange} value={formData.username} className="input-style" placeholder="Seu nome de usuário"/>
                </div>
                <div>
                    <label className="block text-sm font-medium text-gray-300">Nome Completo</label>
                    <input type="text" name="nome_completo" required onChange={handleChange} value={formData.nome_completo} className="input-style" placeholder="Seu nome completo"/>
                </div>
                <div>
                    <label className="block text-sm font-medium text-gray-300">E-mail</label>
                    <input type="email" name="email" required onChange={handleChange} value={formData.email} className="input-style" placeholder="seu@email.com"/>
                </div>
                <div>
                    <label className="block text-sm font-medium text-gray-300">Senha</label>
                    <input type="password" name="password" required onChange={handleChange} value={formData.password} className="input-style" placeholder="••••••••"/>
                </div>
                <div>
                    <label className="block text-sm font-medium text-gray-300">Foto de Perfil (Opcional)</label>
                    <input type="file" name="foto_perfil" onChange={handleFileChange} className="mt-1 block w-full text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-gray-700 file:text-white hover:file:bg-gray-600" />
                </div>
                <div>
                    <button type="submit" className="w-full bg-[#4DA6FF] hover:bg-blue-600 transition-colors text-white font-bold py-3 px-6 rounded-lg text-lg">
                    Avançar
                    </button>
                </div>
            </form>
          </>
        )}

        {step === 2 && (
            <div>
                <TeamSelector
                    onConfirm={handleFinalSubmit}
                    initialSelectedTeamId={formData.time_favorito_id}
                />
                <button onClick={() => setStep(1)} className="w-full mt-4 bg-gray-600 hover:bg-gray-700 transition-colors text-white font-bold py-2 px-4 rounded-lg text-sm">
                    Voltar
                </button>
            </div>
        )}

        <p className="mt-6 text-center text-sm text-gray-400">
          Já tem uma conta?{' '}
          <Link href="/login" className="font-semibold text-[#4DA6FF] hover:underline">
            Faça login
          </Link>
        </p>
      </div>
    </div>
  );
}