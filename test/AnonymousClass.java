class TopLevelClass {
    void method() {
        BaseClass object = new BaseClass() {
            void overriddenMethod1() {
                System.out.println("Overridden");
            }

            void overriddenMethod2() {
                System.out.println("Overridden");
            }
        };
    }
}