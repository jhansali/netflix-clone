import { useCallback, useState } from 'react';
import Input from '@/components/Input'
import axios from 'axios';
import { signIn } from 'next-auth/react';
import { FcGoogle } from 'react-icons/fc';
import { FaGithub } from 'react-icons/fa';

const auth = () => {

    const [email, setEmail] = useState('')
    const [name, setName] = useState('')
    const [password, setPassword] = useState('')
    const [variant, setVariant] = useState('login')
    const toggleVariant = useCallback(() => {
        setVariant((currentVariant) => currentVariant == 'login' ? 'register' : 'login')
    }, [])

    const login = useCallback(async () => {
        try{
            await signIn('credentials', {
                email,
                password,
                callbackUrl: '/profiles'
            });
        }
        catch(error){
            console.error(error)
        }
    }, [email, password]);

    const register = useCallback(async () => {
        try{
            await axios.post('/api/register', {
                email,
                name,
                password
            });
            login();
        }
        catch(error){
            console.error(error)
        }
    }, [email, name, password, login]);

    return(
        <div className="relative h-full w-full bg-[url('/images/hero.jpg')] bg-no-repeat bg-center bg-fixed bg-cover">
            <div className="bg-black w-full h-full lg:bg-opacity-50">
                <nav className="px-12 py-5">
                    <img src="/images/logo.png" alt="Logo" className="h-20 ml-auto mr-auto lg:ml-0 lg:mr-0 lg:h-14"></img>
                </nav>
                <div>
                    <div className="flex justify-center">
                        <div className="bg-black bg-opacity-70 px-16 py-16 self-center mt-2 lg:w-2/5 lg:max-w-md rounded-md w-full">
                            <h2 className="text-white text-4xl mb-8 font-semibold">
                                {variant == 'login' ? 'Sign In' : 'Sign Up'}
                            </h2>
                            <div className="flex flex-col gap-4">
                                {variant == 'register' && (
                                <Input 
                                    label='Username'
                                    onChange={(ev: any) => setName(ev.target.value)}
                                    id='name'
                                    value={name}
                                />
                                )}
                                <Input 
                                    label='Email'
                                    onChange={(ev: any) => setEmail(ev.target.value)}
                                    id='email'
                                    type='email'
                                    value={email}
                                />
                                <Input 
                                    label='Password'
                                    onChange={(ev: any) => setPassword(ev.target.value)}
                                    id='password'
                                    type='password'
                                    value={password}
                                />
                            </div>
                            <button onClick={variant === 'login' ? login:register} className='bg-red-600 py-3 text-white rounded-md w-full mt-10 hover:bg-red-700 transition '>
                                {variant == 'login' ? 'Sign In' : 'Register'}
                            </button>
                            <div className='flex flex-row items-center gap-4 mt-8 justify-center'>
                                <div
                                    onClick={() => signIn('google', {callbackUrl: '/profiles'})}
                                    className='
                                        w-10
                                        h-10
                                        bg-white
                                        rounded-full
                                        flex
                                        items-center
                                        justify-center
                                        cursor-pointer
                                        hover:opacity-80
                                        transition
                                    '>
                                        <FcGoogle size={30}/>
                                </div>
                                <div
                                    onClick={() => signIn('github', {callbackUrl: '/profiles'})}
                                    className='
                                        w-10
                                        h-10
                                        bg-white
                                        rounded-full
                                        flex
                                        items-center
                                        justify-center
                                        cursor-pointer
                                        hover:opacity-80
                                        transition
                                    '>
                                        <FaGithub size={30}/>
                                </div>

                            </div>
                            <p className='text-neutral-500 mt-12'>
                                {variant == 'login' ? 'New to Netflix?' : 'Already have an account?'}
                                <span onClick={toggleVariant} className='text-white ml-1 hover:underline cursor-pointer'>
                                    {variant == 'login' ? 'Sign up now' : 'Sign in'}
                                </span>
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
export default auth;