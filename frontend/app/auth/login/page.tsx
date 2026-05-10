
"use client";



import Link from "next/link";

import { useState } from "react";

import { toast } from "sonner";


import { Button, buttonVariants } from "@/components/ui/button";


import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";


import { Input } from "@/components/ui/input";


import { Label } from "@/components/ui/label";


import { cn } from "@/lib/utils";



export default function LoginPage() {


  const [email, setEmail] = useState("");


  const [password, setPassword] = useState("");





  async function handleSubmit(e: React.FormEvent) {


    e.preventDefault();





    toast.message("Use @supabase/supabase-js with NEXT_PUBLIC_SUPABASE_URL + NEXT_PUBLIC_SUPABASE_ANON_KEY.");





  }






  return (






    <div className="mx-auto max-w-md space-y-6 px-4 py-14">







      <Card>





        <CardHeader>






          <CardTitle>Sign in / Register</CardTitle>



        </CardHeader>



        <CardContent className="space-y-4">












          <form className="space-y-4" onSubmit={handleSubmit}>



            <div>





              <Label htmlFor="email">Email</Label>





              <Input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="mt-1" />





            </div>








            <div>



              <Label htmlFor="password">Password</Label>

















              <Input



                id="password"

















                type="password"

















                value={password}

















                onChange={(e) => setPassword(e.target.value)}

















                className="mt-1"

















              />





            </div>

















            <Button type="submit" className="w-full">












              Submit (stub)






            </Button>














          </form>

















          <Link


            href="/settings"


            className={cn(buttonVariants({ variant: "outline" }), "inline-flex w-full justify-center")}
          >
            Settings




          </Link>














        </CardContent>



      </Card>



    </div>




  );


}
