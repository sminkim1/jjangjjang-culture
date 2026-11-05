import type {Metadata} from 'next';
export const metadata:Metadata={title:'짱짱이 · 우리 아이 첫 문화센터',description:'서울·인천·부천 영유아 문화센터 공식 강좌 비교'};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="ko"><body>{children}</body></html>}
